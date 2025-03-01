import time
import mysql.connector
from mysql.connector import Error
from playwright.sync_api import sync_playwright
from datetime import datetime
import re  # Thêm thư viện re để xử lý regex
from sql.database import connect_database

#! Hàm làm sạch mã chứng khoán
def clean_stock_code(stock_code):
    return re.sub(r'[^A-Za-z0-9]', '', stock_code)  # Giữ lại chỉ các ký tự chữ và số

#! Hàm cuộn trang để tải thêm dữ liệu
def scroll_down(page, scroll_element_selector, step=50, max_height=300):
    scroll_position = 0
    while scroll_position < max_height:
        page.eval_on_selector(scroll_element_selector, f"el => el.scrollTop = {scroll_position}")
        scroll_position += step
        time.sleep(0.5)

#! Hàm lấy dữ liệu tất cả các mã chứng khoán
def fetch_all_stock_data():
    try:
        with sync_playwright() as p:
            # Khởi tạo trình duyệt và trang
            browser = p.chromium.launch(headless=False)  # Hiển thị giao diện để gỡ lỗi
            context = browser.new_context(viewport={"width": 1000, "height": 1000})  # Cấu hình viewport lớn
            page = context.new_page()

            # Truy cập trang web
            page.goto("https://iboard.ssi.com.vn/")
            time.sleep(5)  # Chờ trang tải hoàn toàn

            # Cuộn trang để tải thêm dữ liệu
            scroll_down(page, ".ag-body-viewport", step=100, max_height=500)
            time.sleep(2)

            # Lấy danh sách mã chứng khoán
            stock_code_elements = page.locator("//div[contains(@class, 'ag-cell') and contains(@class, 'stock-symbol')]")
            stock_codes = list(map(lambda el: clean_stock_code(el.inner_text().strip()), stock_code_elements.all()))  # Làm sạch mã chứng khoán
            print(f"Danh sách mã chứng khoán: {stock_codes}")

            # Lấy danh sách giá trần
            ceiling_cells = page.locator("//div[contains(@class, 'ag-cell') and @col-id='ceiling']").all()
            ceiling_prices = [cell.inner_text().strip() for cell in ceiling_cells]
            
            # Lấy danh sách giá sàn
            floor_cells = page.locator("//div[contains(@class, 'ag-cell') and @col-id='floor']").all()
            floor_prices = [cell.inner_text().strip() for cell in floor_cells]

            # Lấy danh sách giá tham chiếu
            tc_cells = page.locator("//div[contains(@class, 'ag-cell') and @col-id='refPrice']").all()
            tc_prices = [cell.inner_text().strip() for cell in tc_cells]

            # # Lấy danh sách tổng khối lượng giao dịch, bỏ qua "Tổng KL"
            # trade_volume_elements = page.locator("//div[contains(@class, 'ag-cell') and @col-id='nmTotalTradedQty']").all()
            # trade_volumes = []
            # for volume in trade_volume_elements:
            #     trade_volume = volume.inner_text().strip()
            #     if trade_volume != "Tổng KL" and trade_volume != "":
            #         trade_volumes.append(trade_volume)

            result = []
            # In ra mã chứng khoán kèm giá trần, giá sàn và giá tham chiếu và tổng khối lượng giao dịch
            for i in range(len(stock_codes)):
                stock_code = stock_codes[i]
                ceiling_price = ceiling_prices[i] if i < len(ceiling_prices) else "Không có giá trần"
                floor_price = floor_prices[i] if i < len(floor_prices) else "Không có giá sàn"
                tc_price = tc_prices[i] if i < len(tc_prices) else "Không có giá tham chiếu"
                # total_traded_qty = trade_volumes[i] if i < len(trade_volumes) else "Không có tổng khối lượng giao dịch"
                
                print(f"Mã chứng khoán: {stock_code}, Giá trần: {ceiling_price}, Giá sàn: {floor_price}, Giá tham chiếu: {tc_price}")
                result.append({
                    "stock_code": stock_code,
                    "ceiling_price": ceiling_price,
                    "floor_price": floor_price,
                    "tc_price": tc_price,
                    # "total_traded_qty": total_traded_qty
                })  

            save_to_mysql(result)
            # Đóng trình duyệt
            browser.close()
            return result
        
    except Exception as e:
        print(f"Lỗi: {e}")

#! Hàm lấy dữ liệu mã chứng khoán cụ thể            
def fetch_single_stock_data(stock_code):
    # Làm sạch mã chứng khoán
    stock_code = clean_stock_code(stock_code)

    try:
        with sync_playwright() as p:
            # Khởi tạo trình duyệt và trang
            browser = p.chromium.launch(headless=False)  # Hiển thị giao diện để gỡ lỗi
            context = browser.new_context(viewport={"width": 1000, "height": 1000})  # Cấu hình viewport lớn
            page = context.new_page()

            # Truy cập trang web
            page.goto("https://iboard.ssi.com.vn/")
            time.sleep(5)  # Chờ trang tải hoàn toàn

            # Cuộn trang để tải thêm dữ liệu
            scroll_down(page, ".ag-body-viewport", step=100, max_height=500)
            time.sleep(2)

            # Lấy danh sách mã chứng khoán
            stock_code_elements = page.locator("//div[contains(@class, 'ag-cell') and contains(@class, 'stock-symbol')]")
            stock_codes = list(map(lambda el: clean_stock_code(el.inner_text().strip()), stock_code_elements.all()))  # Làm sạch mã chứng khoán

            if stock_code not in stock_codes:
                print(f"Mã chứng khoán '{stock_code}' không tồn tại.")
                return None

            # Lấy thông tin cho mã chứng khoán cụ thể
            index = stock_codes.index(stock_code)

            # Lấy danh sách giá trần
            ceiling_cells = page.locator("//div[contains(@class, 'ag-cell') and @col-id='ceiling']").all()
            ceiling_price = ceiling_cells[index].inner_text().strip() if index < len(ceiling_cells) else "Không có giá trần"

            # Lấy danh sách giá sàn
            floor_cells = page.locator("//div[contains(@class, 'ag-cell') and @col-id='floor']").all()
            floor_price = floor_cells[index].inner_text().strip() if index < len(floor_cells) else "Không có giá sàn"

            # Lấy danh sách giá tham chiếu
            tc_cells = page.locator("//div[contains(@class, 'ag-cell') and @col-id='refPrice']").all()
            tc_price = tc_cells[index].inner_text().strip() if index < len(tc_cells) else "Không có giá tham chiếu"

            # # Lấy danh sách tổng khối lượng giao dịch, bỏ qua "Tổng KL"
            # trade_volume_elements = page.locator("//div[contains(@class, 'ag-cell') and @col-id='nmTotalTradedQty']").all()
            # trade_volume = trade_volume_elements[index].inner_text().strip() if index < len(trade_volume_elements) else "Không có tổng khối lượng giao dịch"

            # In ra thông tin mã chứng khoán
            print(f"Mã chứng khoán: {stock_code}, Giá trần: {ceiling_price}, Giá sàn: {floor_price}, Giá tham chiếu: {tc_price}")

            # Đóng trình duyệt
            browser.close()

            return {
                "stock_code": stock_code,
                "ceiling_price": ceiling_price,
                "floor_price": floor_price,
                "tc_price": tc_price,
                # "total_traded_qty": trade_volume
            }

    except Exception as e:
        print(f"Lỗi: {e}")
        return None

# if __name__ == "__main__":
#     fetch_all_stock_data()
#     # Gọi hàm fetch_single_stock_data với mã chứng khoán cụ thể
#     single_stock_data = fetch_single_stock_data("ACB")  # Thay "ACB" bằng mã chứng khoán bạn muốn




#! Kết nối đến cơ sở dữ liệu MySQL
def connect_database():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # Thay đổi mật khẩu nếu cần
            database="stock_ssi"  # Tên cơ sở dữ liệu
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Đã xảy ra lỗi khi kết nối đến MySQL: {err}")
        return None

# #! Hàm kiểm tra dữ liệu trong cơ sở dữ liệu
# def check_data_in_db():
#     db_connection = connect_database()
#     if db_connection is None:
#         print("Không thể kết nối đến MySQL. Thoát.")
#         return
    
#     try:
#         cursor = db_connection.cursor()
#         cursor.execute("SELECT * FROM tracked_stocks_history")
#         result = cursor.fetchall()
#         print(result)
#     except mysql.connector.Error as err:
#         print(f"Đã xảy ra lỗi khi thao tác với MySQL: {err}")
#     finally:
#         cursor.close()
#         db_connection.close()    
    
#! Lưu dữ liệu vào MySQL
def save_to_mysql(result):
    if not result:
        print("Không có dữ liệu để lưu vào MySQL.")
        return

    database_connection = connect_database()
    if database_connection is None:
        print("Không thể kết nối đến MySQL. Thoát.")
        return

    try:
        cursor = database_connection.cursor()

        # Xóa dữ liệu cũ trong bảng `tempory_stocks`
        cursor.execute("DELETE FROM tempory_stocks")
        print("Đã xóa dữ liệu cũ trong bảng `tempory_stocks`.")

        # Chèn dữ liệu mới vào bảng `tempory_stocks` va 'tracked_stocks_history'
        for item in result:
            if item['ceiling_price'] == 'N/A' or item['floor_price'] == 'N/A' or item['tc_price'] == 'N/A':
                print(f"Chưa đủ dữ liệu cho mã {item['stock_code']}. Bỏ qua.")
                continue

            current_time = datetime.now()  # Lấy thời gian hiện tại
            # Chèn dữ liệu vào bảng `tempory_stocks`
            cursor.execute("""
                INSERT INTO tempory_stocks (stock_code, ceiling_price, floor_price, tc_price, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """, (item['stock_code'], item['ceiling_price'], item['floor_price'], item['tc_price'], current_time))
            print(f"Đã chèn thành công mã {item['stock_code']} vào bảng `tempory_stocks`.")

            # Chèn dữ liệu vào bảng `tracked_stocks_history`
            cursor.execute("""
                INSERT INTO tracked_stocks_history (stock_code, ceiling_price, floor_price, tc_price, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """, (item['stock_code'], item['ceiling_price'], item['floor_price'], item['tc_price'], current_time))
            print(f"Đã chèn thành công mã {item['stock_code']} vào bảng `tracked_stocks_history`.")
        # Lưu thay đổi
        database_connection.commit()
        print("Dữ liệu đã được lưu vào cơ sở dữ liệu thành công.")
    
    except mysql.connector.Error as err:
        print(f"Đã xảy ra lỗi khi thao tác với MySQL: {err}")
        database_connection.rollback()
    
    finally:
        cursor.close()
        database_connection.close()
        print("Đóng kết nối MySQL.")


#! Hàm lấy thông tin mã chứng khoán cụ thể thong qua bảng tempory_stocks
def single_stock_data(stock_code):
    db_connection = connect_database()
    if db_connection is None:
        print("Không thể kết nối đến cơ sở dữ liệu.")
        return None

    try:
        cursor = db_connection.cursor(dictionary=True)
        query = "SELECT * FROM tempory_stocks WHERE stock_code = %s"
        cursor.execute(query, (stock_code,))
        result = cursor.fetchall()

        if result:
            print(f"Đã tìm thấy thông tin cho mã {stock_code}: {result}")
            return result
        else:
            print(f"Không tìm thấy thông tin cho mã {stock_code}.")
            return None
    except mysql.connector.Error as err:
        print(f"Đã xảy ra lỗi khi lấy thông tin mã chứng khoán: {err}")
        return None
    finally:
        cursor.close()
        db_connection.close()

#! Hàm lấy tất cả dữ liệu mã chứng khoán từ bảng tempory_stocks
def all_stock_data():
    db_connection = connect_database()
    if db_connection is None:
        print("Không thể kết nối đến cơ sở dữ liệu.")
        return None

    try:
        cursor = db_connection.cursor(dictionary=True)
        query = "SELECT * FROM tempory_stocks ORDER BY stock_code ASC"
        cursor.execute(query)
        results = cursor.fetchall()

        if results:
            print(f"Đã lấy {len(results)} bản ghi từ bảng tempory_stocks.")
            return results
        else:
            print("Không có dữ liệu trong bảng tempory_stocks.")
            return None
    except mysql.connector.Error as err:
        print(f"Đã xảy ra lỗi khi lấy toàn bộ dữ liệu: {err}")
        return None
    finally:
        cursor.close()
        db_connection.close()