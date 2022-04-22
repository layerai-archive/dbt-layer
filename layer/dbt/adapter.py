import json
from pathlib import Path, PurePosixPath
from dataclasses import dataclass
from typing import (
    Optional,
    Tuple,
    Callable,
    Iterable,
    Type,
    Dict,
    Any,
    List,
    Mapping,
    Iterator,
    Union,
    Set,
)
from importlib.machinery import SourceFileLoader
import tempfile

from dbt.adapters.protocol import AdapterConfig
from dbt.adapters.base.relation import BaseRelation
from dbt.clients import agate_helper
from dbt.clients.jinja import MacroGenerator
from dbt.context.providers import generate_runtime_model_context
from dbt.contracts.connection import AdapterResponse
from dbt.contracts.graph.manifest import Manifest, ManifestNode
from dbt.contracts.graph.parsed import ParsedSeedNode
from dbt.events import AdapterLogger
from dbt.exceptions import RuntimeException
from dbt.node_types import NodeType
from dbt.parser.manifest import process_node
from dbt.parser.sql import SqlBlockParser
from dbt.task.sql import SqlCompileRunner

import agate
import pandas as pd

from .sql_parser import LayerSQL, LayerSQLParser

# layer specific code
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
    entrypoint: str = 'handler.py'
    fabric: Optional[str] = None


class LayerAdapter(object):
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
            from dbt.parser.manifest import ManifestLoader
            manifest = ManifestLoader.get_full_manifest(self.config)
            self._manifest_lazy = manifest  # type: ignore[assignment]
        return self._manifest_lazy  # type: ignore[return-value]

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

            self._relation_node_map_lazy = relation_node_map  # type: ignore[assignment]
        return self._relation_node_map_lazy  # type: ignore[return-value]

    def execute(self, sql, **kwargs):
        """
        if the given `sql` represents a Layer build or train, run Layer
        otherwise, pass the `execute` call to the underlying class
        """
        layer_sql = LayerSQLParser.parse(sql)
        if layer_sql is None:
            return super().execute(sql, **kwargs)
        source_node_relation = self._relation_node_map.get(layer_sql.source_name)
        target_node_relation = self._relation_node_map.get(layer_sql.target_name)

        if not source_node_relation:
            raise RuntimeException(f'Unable to find a source named "{layer_sql.source_name}"')
        if not target_node_relation:
            raise RuntimeException(f'Unable to find a target named "{layer_sql.target_name}"')

        source_node, source_relation = source_node_relation
        target_node, target_relation = target_node_relation

        if layer_sql.function_type == 'build':
            return self._run_layer_build(source_node, source_relation, target_node, target_relation)
        elif layer_sql.function_type == 'train':
            return self._run_layer_train(source_node, source_relation, target_node, target_relation)
        # elif layer_sql.function_type == 'infer':
        #     return self._run_layer_infer(source_node, source_relation, target_node, target_relation)
        else:
            raise RuntimeException(f'Unknown layer function "{layer_sql.function_type}"')


    def _run_layer_build(self, source_node, source_relation, target_node, target_relation):
        """
        run Layer and call `load_dataframe` on the returned dataframe
        """
        layer_meta = LayerMeta(**target_node.meta.get('layer', {}))

        # to get the entrypoint absolute path
        # - if entry point is not absolute, append it to the patch_path directory
        # - if entry point is absolute, take it from the project root
        entrypoint = PurePosixPath(layer_meta.entrypoint)

        if entrypoint.is_absolute():
            entrypoint = entrypoint.relative_to(entrypoint.root)
        else:
            _, patch_file_path = target_node.patch_path.split("://")
            entrypoint = Path(patch_file_path).parent / entrypoint

        entrypoint = Path(target_node.root_path) / entrypoint
        logger.debug('Loading Layer entrypoint at {}', entrypoint)

        # load entrypoint
        entrypoint_module = SourceFileLoader(
            f"layer_entrypoint.{target_node.unique_id}", str(entrypoint)).load_module()

        # load source dataframe
        input_df = self._fetch_dataframe(source_node, source_relation)
        logger.debug('Fetched input dataframe - {}', input_df.shape)

        # build the dataframe
        output_df = entrypoint_module.main(input_df)
        logger.debug('Built output dataframe - {}', output_df.shape)

        # save the resulting dataframe to the target
        self._load_dataframe(target_node, target_relation, output_df)

        response = LayerAdapterResponse(
            _message=f'INSERT LAYER DATASET {output_df.size}',
            rows_affected=output_df.size,
            code='LAYER',
        )
        table = agate_helper.empty_table()
        return response, table

    def _run_layer_train(
            self,
            source_node: ManifestNode, source_relation: BaseRelation,
            target_node: ManifestNode, target_relation: BaseRelation
    ) -> Tuple[LayerAdapterResponse, agate.Table]:
        """
        """
        response = LayerAdapterResponse(
            _message='LAYER MODEL',
            rows_affected=0, # TODO
            code='LAYER',
        )
        table = agate_helper.empty_table()
        return response, table

    def _fetch_dataframe(self, node: ManifestNode, relation: BaseRelation) -> pd.DataFrame:
        """
        Fetches all the data from the given node/relation and returns it as a pandas dataframe
        """
        sql = f'select * from {relation.render()}'

        with self.connection_for(node):
            # call super() instead of self to avoid a potential infinite loop
            response, table = super().execute(sql, auto_begin=True, fetch=True)
            super().commit_if_has_connection()
            dataframe = pd.DataFrame.from_records(
                table.rows, columns=table.column_names
            )

        return dataframe

    def _load_dataframe(self, node: ManifestNode, relation: BaseRelation, dataframe: pd.DataFrame) -> None:
        """
        Loads the given pandas dataframe into the given node/relation
        """
        with tempfile.TemporaryDirectory() as tmpdirname:
            path = Path(tmpdirname) / 'data.csv'
            dataframe.to_csv(path)
            table = agate_helper.from_csv(path, node.config.column_types)
            table.original_abspath = path

            materialization_macro = self._manifest.macros['macro.dbt.materialization_seed_default']

            context = generate_runtime_model_context(
                node, self.config, self._manifest
            )
            context['load_agate_table'] = lambda: table
            result = MacroGenerator(materialization_macro, context)()

        return result

    # def load_dataframe(self, database, schema, table_name, agate_table,
    #                    column_override):
    #     print(agate_table)
    #     import traceback
    #     traceback.print_stack()
    #     return
