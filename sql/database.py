import mysql.connector

def connect_db():
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
        print(f"Đã xảy ra lỗi khi kết nối đến MySQL: {err}")
        return None 