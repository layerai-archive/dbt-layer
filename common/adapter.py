import tempfile
from dataclasses import dataclass
from importlib.machinery import SourceFileLoader
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Any, Dict, Mapping, Optional, Tuple

import agate  # type: ignore
import cloudpickle  # type: ignore
import layer
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
from layer.decorators import model as model_decorator

from . import pandas_helper
from .sql_parser import LayerSQLParser


logger = AdapterLogger("Layer")


@dataclass
class LayerAdapterResponse(AdapterResponse):
    """
    Layer Adapter response
    """


@dataclass
class LayerMeta(object):
    """
    Layer meta
    """

    entrypoint: str = "handler.py"
    fabric: Optional[str] = None


class LayerAdapter(BaseAdapter):
    """
    Layer specific overrides
    """

    def __init__(self, config: AdapterConfig):
        super().__init__(config)
        self._manifest_lazy: Optional[Manifest] = None
        self._relation_node_map_lazy: Optional[Mapping[str, ManifestNode]] = None

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

    @property
    def _relation_node_map(self) -> Mapping[str, ManifestNode]:
        if self._relation_node_map_lazy is None:
            return self.load_relation_node_map()
        return self._relation_node_map_lazy

    def load_relation_node_map(self) -> Mapping[str, ManifestNode]:
        if self._relation_node_map_lazy is None:
            relation_node_map = {}

            for node in self._manifest.nodes.values():
                relation = self.Relation.create_from_node(self.config, node)
                relation_node_map[relation.render()] = (node, relation)

            self._relation_node_map_lazy = relation_node_map
        return self._relation_node_map_lazy

    def execute(self, sql: str, **kwargs: Any) -> Tuple[LayerAdapterResponse, agate.Table]:
        """
        if the given `sql` represents a Layer build or train, run Layer
        otherwise, pass the `execute` call to the underlying class
        """
        layer_sql_function = LayerSQLParser().parse(sql)
        if layer_sql_function is None:
            return super().execute(sql, **kwargs)
        source_node_relation = self._relation_node_map.get(layer_sql_function.source_name)
        target_node_relation = self._relation_node_map.get(layer_sql_function.target_name)

        if not source_node_relation:
            raise RuntimeException(f'Unable to find a source named "{layer_sql_function.source_name}"')
        if not target_node_relation:
            raise RuntimeException(f'Unable to find a target named "{layer_sql_function.target_name}"')

        source_node, source_relation = source_node_relation
        target_node, target_relation = target_node_relation

        if layer_sql_function.function_type == "build":
            return self._run_layer_build(source_node, source_relation, target_node, target_relation)
        elif layer_sql_function.function_type == "train":
            return self._run_layer_train(source_node, source_relation, target_node, target_relation)
        elif layer_sql_function.function_type == "predict":
            return self._run_layer_predict(source_node, source_relation, target_node, target_relation)
        else:
            raise RuntimeException(f'Unknown layer function "{layer_sql_function.function_type}"')

    def _run_layer_build(
        self,
        source_node: ManifestNode,
        source_relation: BaseRelation,
        target_node: ManifestNode,
        target_relation: BaseRelation,
    ) -> Tuple[LayerAdapterResponse, agate.Table]:
        """
        Build a dbt model using the given python script
        """
        # load entrypoint
        entrypoint_module = self._get_layer_entrypoint_module(target_node)

        # load source dataframe
        input_df = self._fetch_dataframe(source_node, source_relation)
        logger.debug("Fetched input dataframe - {}", input_df.shape)

        # build the dataframe
        output_df = entrypoint_module.main(input_df)
        logger.debug("Built output dataframe - {}", output_df.shape)

        # save the resulting dataframe to the target
        _, table = self._load_dataframe(target_node, target_relation, output_df)

        response = LayerAdapterResponse(
            _message=f"LAYER DATASET INSERT {output_df.shape[0]}",
            rows_affected=output_df.shape[0],
            code="LAYER",
        )
        return response, table

    def _run_layer_train(
        self,
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
        input_df = self._fetch_dataframe(source_node, source_relation)
        logger.debug("Fetched input dataframe - {}", input_df.shape)

        # build the dataframe
        project_name = self.config.credentials.layer_project
        logger.debug("Training model {}, in project {}", target_node.name, project_name)
        layer.init(project_name)

        def training_func() -> Any:
            return entrypoint_module.main(input_df)

        model_decorator(target_node.name)(training_func)()
        logger.debug("Trained model {}, in project {}", target_node.name, project_name)

        output_df = pd.DataFrame.from_records([[target_node.name]], columns=["name"])

        # save the resulting dataframe to the target
        _, table = self._load_dataframe(target_node, target_relation, output_df)

        response = LayerAdapterResponse(
            _message=f"LAYER MODEL TRAIN {output_df.shape[0]}",
            rows_affected=output_df.shape[0],
            code="LAYER",
        )
        return response, table

    def _run_layer_predict(
        self,
        source_node: ManifestNode,
        source_relation: BaseRelation,
        target_node: ManifestNode,
        target_relation: BaseRelation,
    ) -> Tuple[LayerAdapterResponse, agate.Table]:
        raise NotImplementedError("Prediction not implemented yet!")

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

        entrypoint_module = SourceFileLoader(f"layer_entrypoint.{node.unique_id}", str(entrypoint)).load_module()

        # register this module to be pickled, otherwise pickling fails on dynamically created modules
        cloudpickle.register_pickle_by_value(entrypoint_module)

        return entrypoint_module

    def _fetch_dataframe(self, node: ManifestNode, relation: BaseRelation) -> pd.DataFrame:
        """
        Fetches all the data from the given node/relation and returns it as a pandas dataframe
        """
        # TODO: fix Possible SQL injection vector through string-based query construction. and remove nosec
        sql = f"select * from {relation.render()}"  # nosec

        with self.connection_for(node):
            # call super() instead of self to avoid a potential infinite loop
            response, table = super().execute(sql, auto_begin=True, fetch=True)
            super().commit_if_has_connection()
            dataframe = pandas_helper.from_agate_table(table)

        return dataframe

    def _load_dataframe(
        self, node: ManifestNode, relation: BaseRelation, dataframe: pd.DataFrame
    ) -> Tuple[Dict[Any, Any], agate.Table]:
        """
        Loads the given pandas dataframe into the given node/relation
        """
        with tempfile.TemporaryDirectory() as tmpdirname:
            table = pandas_helper.to_agate_table_with_path(dataframe, Path(tmpdirname) / "data.csv")

            materialization_macro = self._manifest.macros["macro.dbt.materialization_seed_default"]

            context = generate_runtime_model_context(node, self.config, self._manifest)
            context["load_agate_table"] = lambda: table
            result = MacroGenerator(materialization_macro, context)()

        return result, table
