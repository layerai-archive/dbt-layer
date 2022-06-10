import tempfile
from dataclasses import dataclass
from importlib.machinery import SourceFileLoader
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Any, Dict, Optional, Tuple

import agate  # type: ignore
import cloudpickle  # type: ignore
import pandas as pd  # type: ignore
from dbt.adapters.base.impl import BaseAdapter  # type: ignore
from dbt.adapters.base.relation import BaseRelation  # type: ignore
from dbt.adapters.protocol import AdapterConfig  # type: ignore
from dbt.clients.jinja import MacroGenerator  # type: ignore
from dbt.context.providers import generate_runtime_model_context  # type: ignore
from dbt.contracts.connection import AdapterResponse  # type: ignore
from dbt.contracts.graph.manifest import Manifest, ManifestNode  # type: ignore
from dbt.events import AdapterLogger  # type: ignore
from dbt.exceptions import RuntimeException  # type: ignore

import layer
from layer.decorators import model as model_decorator

from . import pandas_helper
from .sql_parser import (
    LayerAutoMLFunction,
    LayerPredictFunction,
    LayerSQLParser,
    LayerTrainFunction,
)


logger = AdapterLogger("Layer")


@dataclass
class LayerAdapterResponse(AdapterResponse):
    """
    Layer Adapter response
    """


@dataclass
class LayerMeta:
    """
    Layer meta
    """

    entrypoint: str = "handler.py"
    fabric: Optional[str] = None


class LayerAdapter(BaseAdapter):  # pylint: disable=abstract-method
    """
    Layer specific overrides
    """

    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        self._manifest_lazy: Optional[Manifest] = None

    @property
    def _manifest(self) -> Manifest:
        if self._manifest_lazy is None:
            return self.load_manifest()
        return self._manifest_lazy

    def load_manifest(self) -> Manifest:
        if self._manifest_lazy is None:
            # avoid a circular import
            from dbt.parser.manifest import ManifestLoader  # type: ignore

            manifest = ManifestLoader.get_full_manifest(self.config)
            self._manifest_lazy = manifest
        return self._manifest_lazy

    def _get_manifest_node_from_relation_name(self, name: str) -> Optional[Tuple[ManifestNode, BaseRelation]]:
        for node in self._manifest.nodes.values():
            for suffix in ["", "__dbt_tmp"]:
                node = node.replace(alias=node.alias + suffix)
                relation = self.Relation.create_from_node(self.config, node)
                if relation.render() == name:
                    return node, relation
        return None

    def execute(
        self, sql: str, auto_begin: bool = False, fetch: bool = False
    ) -> Tuple[LayerAdapterResponse, agate.Table]:
        """
        if the given `sql` represents a Layer build or train, run Layer
        otherwise, pass the `execute` call to the underlying class
        """
        layer_sql_function = LayerSQLParser().parse(sql)
        if layer_sql_function is None:
            return super().execute(sql, auto_begin, fetch)

        source_node_relation = self._get_manifest_node_from_relation_name(layer_sql_function.source_name)
        target_node_relation = self._get_manifest_node_from_relation_name(layer_sql_function.target_name)

        if not source_node_relation:
            raise RuntimeException(f'Unable to find a source named "{layer_sql_function.source_name}" in sql "{sql}"')
        if not target_node_relation:
            raise RuntimeException(f'Unable to find a target named "{layer_sql_function.target_name}" in sql "{sql}"')

        source_node, source_relation = source_node_relation
        target_node, target_relation = target_node_relation

        if isinstance(layer_sql_function, LayerTrainFunction):
            return self._run_layer_train(layer_sql_function, source_node, source_relation, target_node, target_relation)
        elif isinstance(layer_sql_function, LayerPredictFunction):
            return self._run_layer_predict(
                layer_sql_function, source_node, source_relation, target_node, target_relation
            )
        elif isinstance(layer_sql_function, LayerAutoMLFunction):
            return self._run_layer_automl(layer_sql_function, source_node, target_node)
        else:
            raise RuntimeException(f'Unknown layer function "{layer_sql_function.function_type}"')

    def _run_layer_train(
        self,
        layer_sql_function: LayerTrainFunction,
        source_node: ManifestNode,
        source_relation: BaseRelation,
        target_node: ManifestNode,
        target_relation: BaseRelation,
    ) -> Tuple[LayerAdapterResponse, agate.Table]:
        """
        Train a machine learning model using the given python script and save it as a dbt model
        """
        # load entrypoint
        entrypoint_module = self._get_layer_entrypoint_module(target_node)

        # load source dataframe
        raw_input_df = self._fetch_dataframe(source_node, source_relation)
        if layer_sql_function.train_columns == ["*"]:
            input_df = raw_input_df
        else:
            input_df = raw_input_df[layer_sql_function.train_columns].reset_index(drop=True)
        logger.debug("Fetched input dataframe - {}", input_df.shape)

        # login to Layer
        self.login_layer()

        # build the dataframe
        project_name = self.get_project_name(target_node)
        logger.debug("Training model {}, in project {}", target_node.name, project_name)
        layer.init(project_name)

        def training_func() -> Any:
            return entrypoint_module.main(input_df)

        model_decorator(project_name)(training_func)()  # pylint: disable=no-value-for-parameter
        logger.debug("Trained model {}, in project {}", target_node.name, project_name)

        output_df = pd.DataFrame.from_records([[target_node.name]], columns=["name"])

        # save the resulting dataframe to the target
        _, table = self._load_dataframe(target_node, output_df)

        response = LayerAdapterResponse(
            _message=f"LAYER MODEL TRAIN {output_df.shape[0]}",
            rows_affected=output_df.shape[0],
            code="LAYER TRAIN",
        )
        return response, table

    def login_layer(self) -> None:
        layer_api_key = self.config.credentials.layer_api_key
        if layer_api_key is not None:
            layer.login_with_api_key(layer_api_key)
        else:
            raise RuntimeException("Missing credentials: Please configure 'layer_api_key' in your 'profiles.yaml'.")

    def get_project_name(self, node: ManifestNode) -> str:
        if self.config.credentials.layer_project is not None:
            return self.config.credentials.layer_project
        return node.fqn[0]

    @staticmethod
    def _get_layer_meta(node: ManifestNode) -> LayerMeta:
        return LayerMeta(**node.meta.get("layer", {}))

    def _run_layer_automl(
        self,
        param: LayerAutoMLFunction,
        source_node: ManifestNode,
        target_node: ManifestNode,
    ) -> Tuple[LayerAdapterResponse, agate.Table]:
        input_df = self._fetch_dataframe_by_sql(source_node, param.sql)

        model_name = target_node.fqn[-1]

        # login to Layer
        self.login_layer()

        # init project
        project_name = self.get_project_name(target_node)
        logger.debug("Training AutoML model {}, in Layer project {}", model_name, project_name)
        layer.init(project_name)

        from .automl import AutoML

        automl = AutoML(param.model_type, input_df, param.feature_columns, param.target_column)
        automl.train(project_name, model_name)

        response = LayerAdapterResponse(
            _message="LAYER AUTOML COMPLETE",
            rows_affected=0,
            code="LAYER AUTOML",
        )

        output_df = pd.DataFrame(data=[[project_name, model_name]], columns=["project_name", "model_name"])
        _, table = self._load_dataframe(target_node, output_df)

        return response, table

    def _run_layer_predict(
        self,
        layer_sql_function: LayerPredictFunction,
        source_node: ManifestNode,
        source_relation: BaseRelation,
        target_node: ManifestNode,
        target_relation: BaseRelation,
    ) -> Tuple[LayerAdapterResponse, agate.Table]:
        try:
            # load source dataframe
            input_df = self._fetch_dataframe_by_sql(source_node, layer_sql_function.sql)
            logger.debug("Fetched input dataframe - {}", input_df.shape)

            # Users can use the full path for fetching models. If they are authenticated, they can also use the model
            # name as the path. So, we try to log in and init project, only if we have the Layer api key in the dbt
            # profile
            if self.config.credentials.layer_api_key:
                self.login_layer()
                layer.init(self.get_project_name(target_node))

            # Fetch the model
            layer_model_def = layer.get_model(layer_sql_function.model_name)

            model_input = input_df[layer_sql_function.predict_columns]
            predictions = layer_model_def.predict(model_input)
            logger.debug("Prediction dataframe - {}", predictions.shape)
            column_template = layer_sql_function.prediction_alias
            prediction_column_count = len(predictions.columns)
            if prediction_column_count > 1:
                column_template += "_{ix}"
            predictions.columns = [column_template.format(ix=ix) for ix in range(prediction_column_count)]
            select_columns_from_source = list(set(layer_sql_function.select_columns) - set(predictions.columns))
            result_df = pd.concat(
                [
                    input_df[select_columns_from_source].reset_index(drop=True),
                    predictions.reset_index(drop=True),
                ],
                axis=1,
            )

            # save the resulting dataframe to the target
            _, table = self._load_dataframe(target_node, result_df)

            response = LayerAdapterResponse(
                _message=f"LAYER PREDICTION INSERT {predictions.shape[0]}",
                rows_affected=predictions.shape[0],
                code="LAYER PREDICT",
            )
            return response, table
        except Exception as e:
            import traceback

            traceback.print_exc()
            raise e

    def _get_layer_entrypoint_module(self, node: ManifestNode) -> ModuleType:
        """
        get the entrypoint absolute path
        - if entry point is not absolute, append it to the patch_path directory
        - if entry point is absolute, take it from the project root

        then load the module at that path
        """

        layer_meta = LayerMeta(**node.meta.get("layer", {}))

        entrypoint = PurePosixPath(layer_meta.entrypoint)

        if entrypoint.is_absolute():
            entrypoint = entrypoint.relative_to(entrypoint.root)
        else:
            _, patch_file_path = node.patch_path.split("://")
            entrypoint = PurePosixPath(patch_file_path).parent / entrypoint

        entrypoint = PurePosixPath(node.root_path) / entrypoint
        logger.debug("Loading Layer entrypoint at {}", entrypoint)

        entrypoint_module = SourceFileLoader(  # pylint: disable=deprecated-method
            f"layer_entrypoint.{node.unique_id}", str(entrypoint)
        ).load_module(None)

        # register this module to be pickled, otherwise pickling fails on dynamically created modules
        cloudpickle.register_pickle_by_value(entrypoint_module)

        return entrypoint_module

    def _fetch_dataframe(self, node: ManifestNode, relation: BaseRelation) -> pd.DataFrame:
        """
        Fetches all the data from the given node/relation and returns it as a pandas dataframe
        """
        # TODO: fix Possible SQL injection vector through string-based query construction. and remove nosec
        sql = f"select * from {relation.render()}"  # nosec
        return self._fetch_dataframe_by_sql(node=node, sql=sql)

    def _fetch_dataframe_by_sql(self, node: ManifestNode, sql: str) -> pd.DataFrame:
        """
        Fetches all the data from the given sql and returns it as a pandas dataframe
        """
        with self.connection_for(node):
            # call super() instead of self to avoid a potential infinite loop
            unused_response, table = super().execute(sql, auto_begin=True, fetch=True)
            super().commit_if_has_connection()
            dataframe = pandas_helper.from_agate_table(table)

        return dataframe

    def _load_dataframe(self, node: ManifestNode, dataframe: pd.DataFrame) -> Tuple[Dict[Any, Any], agate.Table]:
        """
        Loads the given pandas dataframe into the given node/relation
        """
        with tempfile.TemporaryDirectory() as tmpdirname:
            file = Path(tmpdirname) / "data.csv"
            table = pandas_helper.to_agate_table_with_path(dataframe, file)

            materialization_macro = self._manifest.macros["macro.dbt.materialization_seed_default"]

            context = generate_runtime_model_context(node, self.config, self._manifest)
            context["load_agate_table"] = lambda: table
            result = MacroGenerator(materialization_macro, context)()

        return result, table
