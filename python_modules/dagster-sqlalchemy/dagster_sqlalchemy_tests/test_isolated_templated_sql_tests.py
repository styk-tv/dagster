from dagster import (
    DependencyDefinition,
    PipelineContextDefinition,
    PipelineDefinition,
    execute_pipeline,
)

from dagster_sqlalchemy.templated import (
    _render_template_string,
    create_templated_sql_transform_solid,
)

from dagster.core.utility_solids import define_stub_solid

from .math_test_db import in_mem_context_params


def _load_table(context, table_name):
    return (
        context.resources.sa.engine.connect()
        .execute('SELECT * FROM {table_name}'.format(table_name=table_name))
        .fetchall()
    )


def pipeline_test_def(solids, context_params, dependencies=None):
    return PipelineDefinition(
        solids=solids,
        context_definitions={
            'default': PipelineContextDefinition(context_fn=lambda info: context_params)
        },
        dependencies=dependencies,
    )


def define_sum_table_pipeline():
    sql = '''CREATE TABLE {{sum_table}} AS
    SELECT num1, num2, num1 + num2 as sum FROM num_table'''

    sum_table_transform = create_templated_sql_transform_solid(
        name='sum_table_transform', sql=sql, table_arguments=['sum_table']
    )

    pipeline = pipeline_test_def(
        solids=[sum_table_transform], context_params=in_mem_context_params()
    )
    return pipeline


def test_single_templated_sql_solid_single_table_with_api():
    pipeline = define_sum_table_pipeline()

    sum_table_arg = 'specific_sum_table'

    environment = {'solids': {'sum_table_transform': {'config': {'sum_table': sum_table_arg}}}}

    result = execute_pipeline(pipeline, environment=environment)
    assert result.success

    assert _load_table(result.context, sum_table_arg) == [(1, 2, 3), (3, 4, 7)]


def test_single_templated_sql_solid_double_table_raw_api():
    sum_table_arg = 'specific_sum_table'
    num_table_arg = 'specific_num_table'

    sql = '''CREATE TABLE {{sum_table}} AS
        SELECT num1, num2, num1 + num2 as sum FROM {{num_table}}'''

    sum_solid = create_templated_sql_transform_solid(
        name='sum_solid', sql=sql, table_arguments=['sum_table', 'num_table']
    )

    pipeline = pipeline_test_def(
        solids=[sum_solid], context_params=in_mem_context_params(num_table_arg)
    )

    environment = {
        'solids': {
            'sum_solid': {'config': {'sum_table': sum_table_arg, 'num_table': num_table_arg}}
        }
    }

    result = execute_pipeline(pipeline, environment=environment)
    assert result.success

    assert _load_table(result.context, sum_table_arg) == [(1, 2, 3), (3, 4, 7)]


def test_single_templated_sql_solid_double_table_with_api():
    sum_table_arg = 'specific_sum_table'
    num_table_arg = 'specific_num_table'

    sql = '''CREATE TABLE {{sum_table}} AS
    SELECT num1, num2, num1 + num2 as sum FROM {{num_table}}'''

    sum_solid = create_templated_sql_transform_solid(
        name='sum_solid', sql=sql, table_arguments=['sum_table', 'num_table']
    )

    pipeline = pipeline_test_def(
        solids=[sum_solid], context_params=in_mem_context_params(num_table_arg)
    )

    environment = {
        'solids': {
            'sum_solid': {'config': {'sum_table': sum_table_arg, 'num_table': num_table_arg}}
        }
    }

    result = execute_pipeline(pipeline, environment=environment)
    assert result.success

    assert _load_table(result.context, sum_table_arg) == [(1, 2, 3), (3, 4, 7)]

    assert (
        result.result_for_solid('sum_solid').transformed_value('sql_text')
        == '''CREATE TABLE specific_sum_table AS
    SELECT num1, num2, num1 + num2 as sum FROM specific_num_table'''
    )


def test_templated_sql_solid_pipeline():
    sum_sql_template = '''CREATE TABLE {{sum_table}} AS
        SELECT num1, num2, num1 + num2 as sum FROM num_table'''

    sum_sq_sql_template = '''CREATE TABLE {{sum_sq_table}} AS
        SELECT num1, num2, sum, sum * sum as sum_sq FROM {{sum_table}}'''

    sum_solid = create_templated_sql_transform_solid(
        name='sum_table', sql=sum_sql_template, table_arguments=['sum_table']
    )

    sum_sq_solid = create_templated_sql_transform_solid(
        name='sum_sq_table',
        sql=sum_sq_sql_template,
        table_arguments=['sum_table', 'sum_sq_table'],
        dependant_solids=[sum_solid],
    )

    context = in_mem_context_params()

    pipeline = pipeline_test_def(
        solids=[sum_solid, sum_sq_solid],
        context_params=context,
        dependencies={sum_sq_solid.name: {sum_solid.name: DependencyDefinition(sum_solid.name)}},
    )
    first_sum_table = 'first_sum_table'
    first_sum_sq_table = 'first_sum_sq_table'

    environment_one = {
        'solids': {
            'sum_table': {'config': {'sum_table': first_sum_table}},
            'sum_sq_table': {
                'config': {'sum_table': first_sum_table, 'sum_sq_table': first_sum_sq_table}
            },
        }
    }

    first_result = execute_pipeline(pipeline, environment=environment_one)
    assert first_result.success

    assert len(first_result.result_list) == 2
    assert first_result.result_list[0].transformed_value() == {'sum_table': first_sum_table}
    assert first_result.result_list[1].transformed_value() == {
        'sum_table': first_sum_table,
        'sum_sq_table': first_sum_sq_table,
    }

    assert _load_table(first_result.context, first_sum_table) == [(1, 2, 3), (3, 4, 7)]

    assert _load_table(first_result.context, first_sum_sq_table) == [(1, 2, 3, 9), (3, 4, 7, 49)]

    # now execute subdag

    pipeline_two = pipeline_test_def(
        solids=[define_stub_solid('pass_value', 'TODO'), sum_sq_solid],
        context_params=context,
        dependencies={sum_sq_solid.name: {sum_solid.name: DependencyDefinition('pass_value')}},
    )

    second_sum_sq_table = 'second_sum_sq_table'

    sum_sq_args = {'sum_table': first_sum_table, 'sum_sq_table': second_sum_sq_table}

    environment_two = {'solids': {'sum_sq_table': {'config': sum_sq_args}}}

    second_result = execute_pipeline(pipeline_two, environment=environment_two)
    assert second_result.success
    assert len(second_result.result_list) == 2
    assert _load_table(second_result.context, second_sum_sq_table) == [(1, 2, 3, 9), (3, 4, 7, 49)]


def test_templated_sql_solid_with_api():
    sql_template = '''CREATE TABLE {{sum_table}} AS
        SELECT num1, num2, num1 + num2 as sum FROM num_table'''

    sum_solid = create_templated_sql_transform_solid(
        name='sum_solid', sql=sql_template, table_arguments=['sum_table']
    )

    pipeline = pipeline_test_def(solids=[sum_solid], context_params=in_mem_context_params())

    sum_table_arg = 'specific_sum_table'

    environment = {'solids': {'sum_solid': {'config': {'sum_table': sum_table_arg}}}}

    result = execute_pipeline(pipeline, environment=environment)
    assert result.success

    assert _load_table(result.context, sum_table_arg) == [(1, 2, 3), (3, 4, 7)]


def test_with_from_through_specifying_all_solids():
    pipeline = create_multi_input_pipeline()

    first_sum_table = 'first_sum_table'
    first_mult_table = 'first_mult_table'
    first_sum_mult_table = 'first_sum_mult_table'

    environment = {
        'solids': {
            'sum_table': {'config': {'sum_table': first_sum_table}},
            'mult_table': {'config': {'mult_table': first_mult_table}},
            'sum_mult_table': {
                'config': {
                    'sum_table': first_sum_table,
                    'mult_table': first_mult_table,
                    'sum_mult_table': first_sum_mult_table,
                }
            },
        }
    }

    pipeline_result = execute_pipeline(pipeline, environment=environment)
    assert len(pipeline_result.result_list) == 3
    assert _load_table(pipeline_result.context, first_sum_table) == [(1, 2, 3), (3, 4, 7)]
    assert _load_table(pipeline_result.context, first_mult_table) == [(1, 2, 2), (3, 4, 12)]
    assert _load_table(pipeline_result.context, first_sum_mult_table) == [(1, 3, 2), (3, 7, 12)]


def test_multi_input_partial_execution():
    pipeline = create_multi_input_pipeline()

    first_sum_table = 'first_sum_table'
    first_mult_table = 'first_mult_table'
    first_sum_mult_table = 'first_sum_mult_table'

    environment = {
        'solids': {
            'sum_table': {'config': {'sum_table': first_sum_table}},
            'mult_table': {'config': {'mult_table': first_mult_table}},
            'sum_mult_table': {
                'config': {
                    'sum_table': first_sum_table,
                    'mult_table': first_mult_table,
                    'sum_mult_table': first_sum_mult_table,
                }
            },
        }
    }

    first_pipeline_result = execute_pipeline(pipeline, environment=environment)

    assert first_pipeline_result.success
    assert len(first_pipeline_result.result_list) == 3
    assert _load_table(first_pipeline_result.context, first_sum_table) == [(1, 2, 3), (3, 4, 7)]
    assert _load_table(first_pipeline_result.context, first_mult_table) == [(1, 2, 2), (3, 4, 12)]
    assert _load_table(first_pipeline_result.context, first_sum_mult_table) == [
        (1, 3, 2),
        (3, 7, 12),
    ]


def create_multi_input_pipeline():
    sum_sql_template = '''CREATE TABLE {{sum_table}} AS
        SELECT num1, num2, num1 + num2 as sum FROM num_table'''

    mult_sql_template = '''CREATE TABLE {{mult_table}} AS
        SELECT num1, num2, num1 * num2 as mult FROM num_table'''

    sum_mult_join_template = '''CREATE TABLE {{sum_mult_table}} AS
        SELECT {{sum_table}}.num1, sum, mult FROM {{sum_table}}
        INNER JOIN {{mult_table}} ON {{sum_table}}.num1 = {{mult_table}}.num1'''

    sum_solid = create_templated_sql_transform_solid(
        name='sum_table', sql=sum_sql_template, table_arguments=['sum_table']
    )

    mult_solid = create_templated_sql_transform_solid(
        name='mult_table', sql=mult_sql_template, table_arguments=['mult_table']
    )

    sum_mult_solid = create_templated_sql_transform_solid(
        name='sum_mult_table',
        sql=sum_mult_join_template,
        table_arguments=['sum_table', 'mult_table', 'sum_mult_table'],
        dependant_solids=[sum_solid, mult_solid],
    )

    pipeline = pipeline_test_def(
        solids=[sum_solid, mult_solid, sum_mult_solid],
        context_params=in_mem_context_params(),
        dependencies={
            sum_mult_solid.name: {
                sum_solid.name: DependencyDefinition(sum_solid.name),
                mult_solid.name: DependencyDefinition(mult_solid.name),
            }
        },
    )
    return pipeline


def test_jinja():
    templated_sql = '''SELECT * FROM {{some_table.name}}'''

    sql = _render_template_string(templated_sql, {'some_table': {'name': 'fill_me_in'}})

    assert sql == '''SELECT * FROM fill_me_in'''
