from typing import Callable, List, Union


def extract(endpoint: Callable, *args, **kwargs) -> Union[dict, List[dict]]:
    """
    Parameters
    ----------
    endpoint : Callable
        API endpoint to be called.
    """
    return endpoint(*args, **kwargs)


def transform(
    data: Union[dict, List[dict]],
    func: Callable[[dict], dict],
    keys: List[str],
) -> Union[dict, List[dict]]:
    """
    Transform data for intended use case.
    """

    if isinstance(data, dict):
        data = func(data)
        return {k: data[k] for k in keys}
    elif isinstance(data, list):
        transformed_data = []
        for d in data:
            d = func(d)
            transformed_data.append({k: d[k] for k in keys})
        return transformed_data
    else:
        raise TypeError


def load(data: Union[dict, List[dict]], sql: str, con) -> None:
    """
    Load data into a database.

    Parameters
    ----------
    data : Union[dict, List[dict]]
        Transformed data.
    sql : str
        SQL INSERT INTO statement.
    con :
        Database connection.
    """
    cursor = con.cursor()

    if isinstance(data, dict):
        cursor.execute(sql, data)
    elif isinstance(data, list):
        for d in data:
            cursor.execute(sql, d)
    else:
        raise TypeError
