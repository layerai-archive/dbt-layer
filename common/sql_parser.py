from typing import Any, Callable, List, Optional, Tuple

import sqlparse  # type:ignore
from sqlparse.sql import Token  # type:ignore
from sqlparse.tokens import Name, Newline, Punctuation  # type:ignore
from sqlparse.utils import remove_quotes  # type:ignore


class LayerSqlFunction:
    """
    A parsed Layer SQL statement
    """

    SUPPORTED_FUNCTION_TRAIN = "train"
    SUPPORTED_FUNCTION_PREDICT = "predict"
    SUPPORTED_FUNCTION_AUTOML = "automl"
    SUPPORTED_FUNCTION_TYPES = [SUPPORTED_FUNCTION_TRAIN, SUPPORTED_FUNCTION_PREDICT, SUPPORTED_FUNCTION_AUTOML]

    def __init__(self, function_type: str, source_name: str, target_name: str) -> None:
        self.function_type = function_type
        self.source_name = source_name
        self.target_name = target_name

    def __repr__(self) -> str:
        return (
            f"<LayerSQL function_type:{self.function_type}"
            + f" source_name:{self.source_name}"
            + f" target_name:{self.target_name}>"
        )


class LayerPredictFunction(LayerSqlFunction):
    def __init__(
        self,
        source_name: str,
        target_name: str,
        model_name: str,
        select_columns: List[str],
        predict_columns: List[str],
        prediction_alias: str,
        sql: str,
    ) -> None:
        super().__init__(
            function_type=self.SUPPORTED_FUNCTION_PREDICT, source_name=source_name, target_name=target_name
        )
        self.model_name = model_name
        self.select_columns = select_columns
        self.predict_columns = predict_columns
        self.prediction_alias = prediction_alias
        self.sql = sql


class LayerTrainFunction(LayerSqlFunction):
    def __init__(
        self,
        source_name: str,
        target_name: str,
        train_columns: List[str],
    ) -> None:
        super().__init__(function_type=self.SUPPORTED_FUNCTION_TRAIN, source_name=source_name, target_name=target_name)
        self.train_columns = train_columns


class LayerAutoMLFunction(LayerSqlFunction):
    def __init__(
        self,
        source_name: str,
        target_name: str,
        model_type: str,
        feature_columns: List[str],
        target_column: str,
        sql: str,
    ) -> None:
        super().__init__(function_type=self.SUPPORTED_FUNCTION_AUTOML, source_name=source_name, target_name=target_name)
        self.feature_columns = feature_columns
        self.target_column = target_column
        self.model_type = model_type
        self.sql = sql


def find_from_token(tokens: List[Token]) -> List[Token]:
    return expect_tokens(tokens, [keyword("from"), lambda x: isinstance(x, sqlparse.sql.Identifier)])


def get_from_where_clause(select_tokens: List[Token]) -> Tuple[str, str]:
    from_token = find_from_token(select_tokens)
    if not from_token:
        raise ValueError("Invalid sql. Missing 'from' clause.")
    source = from_token[0].value
    where_statement = " ".join((x.value for x in from_token[1:]))
    return source, where_statement


def get_cols_from_container(brace_container_token: Token) -> List[str]:
    _, cols_token, _ = brace_container_token.tokens
    if isinstance(cols_token, sqlparse.sql.IdentifierList):
        return [x.value for x in clean_separators(cols_token.tokens)]
    return [cols_token.value]


def build_sql(cols: List[str], source: str, where_statement: str) -> str:
    col_str = ", ".join(cols)
    if len(where_statement) > 0:
        return f"select {col_str} from {source} {where_statement}"
    else:
        return f"select {col_str} from {source}"


class LayerSQLParser:

    ALL_COLUMNS_WILDCARD = "*"

    def parse(self, sql: str) -> Optional[LayerSqlFunction]:
        """
        returns None if not a layer SQL statement
        returns an instance of LayerSQL if a valid layer SQL statement
        """
        parsed = sqlparse.parse(sql)
        if not parsed:
            return None

        tokens = parsed[0].tokens
        layer_func = next((x for x in find_functions(tokens) if is_layer_function(x)), None)
        if not layer_func:
            return None

        target_name_group = next((x for x in expect_tokens(tokens, [keyword("create or replace"), group()])), None)
        if not target_name_group:
            return None
        target_name = self._get_target_name_from_group(target_name_group)

        if is_automl_function(layer_func):
            return self.parse_automl(layer_func, target_name)
        elif is_predict_function(layer_func):
            return self.parse_predict(layer_func, target_name)
        elif is_train_function(layer_func):
            return self.parse_train(layer_func, target_name)
        else:
            raise ValueError(f"Unsupported function: {layer_func.get_name()}")

    def _get_target_name_from_group(self, token: Token) -> str:
        clean_inner_tokens = remove_tokens(token.flatten(), newline())
        target_name_tokens = slice_between_tokens(clean_inner_tokens, name(), whitespace())
        if target_name_tokens:
            return "".join([x.value for x in target_name_tokens])
        else:
            raise ValueError("Invalid sql syntax")

    def parse_predict(self, layer_func_token: Token, target: str) -> LayerPredictFunction:

        # We need the parent `select` statement that contains the function
        # to get access to the selected columns and the source relation
        select_sttmt = find_parent(layer_func_token, lambda x: isinstance(x, sqlparse.sql.Parenthesis))
        clean_select_sttmt = []
        if not select_sttmt:
            raise ValueError("SQL syntax error")
        else:
            clean_select_sttmt = clean_separators(select_sttmt.tokens)

        # sqlparse doesn't seem to parse correctly the inner contents of this parenthesis.
        # Here, we rebuild the sql and use parse it again to get the relevant tokens
        inner_sql_text = " ".join(x.value for x in clean_select_sttmt)
        inner_sql = sqlparse.parse(inner_sql_text)[0]
        clean_inner_sql = remove_tokens(inner_sql.tokens, lambda x: x.is_whitespace)

        source, where_statement = get_from_where_clause(clean_inner_sql)

        # extract the selected columns in the query
        columns_incl_layer = []
        select_columns_list = find_token(clean_inner_sql, lambda x: isinstance(x, sqlparse.sql.IdentifierList))
        if select_columns_list is None:
            raise ValueError("SQL syntax error. Select columns are missing.")
        else:
            columns_incl_layer = find_tokens(
                select_columns_list.tokens, lambda x: isinstance(x, sqlparse.sql.Identifier)
            )
        columns = remove_tokens(columns_incl_layer, lambda t: find_layer_function(t) is not None)
        select_columns = [t.value for t in columns]

        # extract the layer prediction function
        clean_func_tokens = clean_separators(layer_func_token[1].tokens)
        if len(clean_func_tokens) < 3:
            invalid_func = " ".join(t.value for t in clean_func_tokens)
            raise ValueError(f"Invalid predict function syntax {invalid_func}")
        model_name, _, bracket_container = clean_func_tokens
        predict_model = remove_quotes(model_name.value)
        predict_cols = get_cols_from_container(bracket_container)

        all_columns = select_columns + list(set(predict_cols) - set(select_columns))
        sql_text = build_sql(all_columns, source, where_statement)
        sql = sqlparse.format(sql_text, keyword_case="lower", strip_whitespace=True)

        prediction_alias = layer_func_token.parent.get_alias() or "prediction"

        return LayerPredictFunction(
            source,
            target,
            predict_model,
            select_columns,
            predict_cols,
            prediction_alias,
            sql,
        )

    def parse_automl(self, layer_func_token: Token, target: str) -> LayerAutoMLFunction:

        # We need the parent `select` statement that contains the function
        # to get access to the selected columns and the source relation
        select_sttmt = find_parent(layer_func_token, lambda x: isinstance(x, sqlparse.sql.Parenthesis))
        clean_select_sttmt = []
        if not select_sttmt:
            raise ValueError("SQL syntax error")
        else:
            clean_select_sttmt = clean_separators(select_sttmt.tokens)

        # sqlparse doesn't seem to parse correctly the inner contents of this parenthesis.
        # Here, we rebuild the sql and use parse it again to get the relevant tokens
        inner_sql_text = " ".join(x.value for x in clean_select_sttmt)
        inner_sql = sqlparse.parse(inner_sql_text)[0]
        clean_inner_sql = remove_tokens(inner_sql.tokens, lambda x: x.is_whitespace)

        source, where_statement = get_from_where_clause(clean_inner_sql)

        # extract the layer prediction function
        clean_func_tokens = clean_separators(layer_func_token[1].tokens)
        if len(clean_func_tokens) < 4:
            invalid_func = " ".join(t.value for t in clean_func_tokens)
            raise ValueError(f"Invalid automl function syntax {invalid_func}")
        model_type_token, _, bracket_container, target_column_token = clean_func_tokens
        model_type = remove_quotes(model_type_token.value)
        feature_columns = get_cols_from_container(bracket_container)
        target_column = remove_quotes(target_column_token.value)
        all_columns = list(dict.fromkeys((feature_columns + [target_column])))
        sql_text = build_sql(all_columns, source, where_statement)
        sql = sqlparse.format(sql_text, keyword_case="lower", strip_whitespace=True)

        return LayerAutoMLFunction(source, target, model_type, feature_columns, target_column, sql)

    def parse_train(self, layer_func_token: Token, target: str) -> LayerTrainFunction:
        select = find_parent(layer_func_token, lambda x: isinstance(x, sqlparse.sql.Identifier))
        if not select:
            raise ValueError("SQL syntax error")
        else:
            clean_select = clean_separators(select)
            source, _ = get_from_where_clause(layer_func_token.parent.parent.tokens)
            _, train_func = clean_select
            if len(train_func.tokens) < 2:
                invalid_func = "".join(x.value for x in select.flatten())
                raise ValueError(f"Invalid train function syntax {invalid_func}")
            _, parenthesis_group = train_func.tokens
            cols = self.extract_columns(clean_separators(parenthesis_group.tokens))

            return LayerTrainFunction(source, target, cols)

    def extract_columns(self, content_tokens: List[Token]) -> List[str]:
        if len(content_tokens) < 1:
            return [self.ALL_COLUMNS_WILDCARD]
        if content_tokens[0].value.lower() == "array":
            if len(content_tokens) < 2:
                raise ValueError("Invalid train function syntax")
            identifiers = clean_separators(content_tokens[1].tokens)[0]
            return [x.value for x in identifiers.get_identifiers()]
        else:
            return [content_tokens[0].value]


# Functions to assist the SQL Parsing


TokenPredicate = Callable[[Token], bool]


def get_predict_function_name(layer_column_token: Token) -> Optional[str]:
    if layer_column_token.has_alias():
        return layer_column_token.get_name()
    return "predict"


def find_token(tokens: List[Token], pred: TokenPredicate) -> Optional[Token]:
    for token in tokens:
        if pred(token):
            return token
    return None


def find_tokens(tokens: List[Token], pred: TokenPredicate) -> List[Token]:
    return [x for x in tokens if pred(x)]


def remove_tokens(tokens: List[Token], pred: TokenPredicate) -> List[Token]:
    return [x for x in tokens if not pred(x)]


def clean_separators(tokens: List[Token]) -> List[Token]:
    return remove_tokens(tokens, lambda x: x.is_whitespace or x.ttype == Punctuation)


def expect_tokens(tokens: List[Token], predicates: List[TokenPredicate]) -> List[Token]:
    if not tokens or not predicates:
        return tokens
    pred = predicates[0]
    for i, token in enumerate(tokens):
        if pred(token):
            return expect_tokens(tokens[i:], predicates[1:])
    return []


def slice_between_tokens(tokens: List[Token], start: TokenPredicate, end: TokenPredicate) -> Optional[List[Token]]:
    if not tokens:
        return None
    start_index = -1
    end_index = -1
    start_seen = False
    for i, token in enumerate(tokens):
        if not start_seen and start(token):
            start_index = i
            start_seen = True
        if start_seen and end(token):
            end_index = i
            break
    if start_index >= 0 and end_index > 0:
        return tokens[start_index:end_index]
    else:
        return None


def find_functions(elem: Any) -> List[Token]:
    from itertools import chain

    funcs: List[List[Token]] = [[]]
    if isinstance(elem, List):
        funcs = [find_functions(x) for x in elem]
    elif isinstance(elem, sqlparse.sql.Statement):
        funcs = [find_functions(x) for x in elem.tokens]
    elif isinstance(elem, sqlparse.sql.IdentifierList):
        funcs = [find_functions(x) for x in elem.get_identifiers()]
    elif isinstance(elem, sqlparse.sql.Identifier):
        funcs = [find_functions(x) for x in elem.tokens]
    elif isinstance(elem, sqlparse.sql.Parenthesis):
        funcs = [find_functions(x) for x in elem.tokens]
    elif isinstance(elem, sqlparse.sql.Function):
        return [elem]
    return list(chain.from_iterable(funcs))


def find_parent(token: Token, pred: TokenPredicate) -> Optional[Token]:
    parent = token.parent
    if not parent:
        return None
    elif pred(parent):
        return parent
    else:
        return find_parent(parent, pred)


def is_layer_function(func: sqlparse.sql.Function) -> bool:
    parent = func.parent
    return isinstance(parent, sqlparse.sql.Identifier) and parent.tokens[0].value == "layer"


def find_layer_function(tokens: List[Token]) -> Optional[Token]:
    return next((x for x in find_functions(tokens) if is_layer_function(x)), None)


def is_predict_function(func: sqlparse.sql.Function) -> bool:
    return func[0].value.lower() == LayerSqlFunction.SUPPORTED_FUNCTION_PREDICT


def is_automl_function(func: sqlparse.sql.Function) -> bool:
    return func[0].value.lower() == LayerSqlFunction.SUPPORTED_FUNCTION_AUTOML


def is_train_function(func: sqlparse.sql.Function) -> bool:
    return func[0].value.lower() == LayerSqlFunction.SUPPORTED_FUNCTION_TRAIN


def keyword(value: str) -> TokenPredicate:
    def check_token(token: Token) -> bool:
        return token.is_keyword and token.value.lower() == value.lower()

    return check_token


def whitespace() -> Callable[[Token], bool]:
    return lambda x: x.is_whitespace


def name() -> Callable[[Token], bool]:
    return lambda x: x.ttype is Name


def newline() -> Callable[[Token], bool]:
    return lambda x: x.ttype is Newline


def group() -> Callable[[Token], bool]:
    return lambda x: x.is_group
