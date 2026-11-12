from unittest.mock import MagicMock, patch


def _import_app_without_postgres():
    connection = MagicMock()
    connection.__enter__.return_value = connection
    cursor = MagicMock()
    cursor.__enter__.return_value = cursor
    cursor.fetchone.return_value = {"count": 1}
    connection.cursor.return_value.__enter__.return_value = cursor

    with patch("psycopg.connect", return_value=connection):
        import main

    return main.app


app = _import_app_without_postgres()
