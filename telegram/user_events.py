import mysql.connector
import logging

# Function to connect to the database
def connect_database():
    # Kết nối đến cơ sở dữ liệu MySQL
    try:
        connection = mysql.connector.connect(
            host="localhost",        # Địa chỉ máy chủ MySQL
            user="root",             # Tên người dùng MySQL
            password="",             # Mật khẩu của bạn
            database="stock_ssi" # Tên cơ sở dữ liệu
        )
        return connection
    except mysql.connector.Error as err:
        logging.error(f"Error connecting to MySQL: {err}")
        return None

# Function to log user events
def log_user_event(user_id, username, command, details, chat_id):
    connection = connect_database()
    if connection is None:
        logging.error("Cannot connect to the database.")
        return

    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO user_events (user_id, username, command, details, chat_id)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, username, command, details, chat_id))
        connection.commit()
    except mysql.connector.Error as err:
        logging.error(f"Error logging user event: {err}")
    finally:
        cursor.close()
        connection.close()