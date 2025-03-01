import time
from playwright.sync_api import sync_playwright
from datetime import datetime
import re  # Thêm thư viện re để xử lý regex
    
#! Hàm làm sạch mã chứng khoán
def clean_stock_code(stock_code):
    return re.sub(r'[^A-Za-z0-9]', '', stock_code)  # Giữ lại chỉ các ký tự chữ và số
#! hàm cuon trang
def scroll_down(page, scroll_element_selector, step=50, max_height=300):
    scroll_position = 0
    while scroll_position < max_height:
        page.eval_on_selector(scroll_element_selector, f"el => el.scrollTop = {scroll_position}")
        scroll_position += step
        time.sleep(0.5)

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

            #lấy giá bán 1
            best1offer_cells = page.locator("//div[contains(@class, 'ag-cell') and @col-id='best1Offer']").all()
            best1offer_prices = [cell.inner_text().strip() for cell in best1offer_cells]


            # Lấy danh sách tổng khối lượng giao dịch, bỏ qua "Tổng KL"
            trade_volume_elements = page.locator("//div[contains(@class, 'ag-cell') and @col-id='nmTotalTradedQty']").all()
            trade_volumes = []
            for volume in trade_volume_elements:
                trade_volume = volume.inner_text().strip()
                if trade_volume != "Tổng KL" and trade_volume != "":
                    trade_volumes.append(trade_volume)

            result = []
            # In ra mã chứng khoán kèm giá trần, giá sàn và giá tham chiếu và tổng khối lượng giao dịch
            for i in range(len(stock_codes)):
                stock_code = stock_codes[i]
                ceiling_price = ceiling_prices[i] if i < len(ceiling_prices) else "Không có giá trần"
                floor_price = floor_prices[i] if i < len(floor_prices) else "Không có giá sàn"
                tc_price = tc_prices[i] if i < len(tc_prices) else "Không có giá tham chiếu"
                best1offer_price = best1offer_prices[i] if i < len(best1offer_prices) else "Không có giá bán 1"
                total_traded_qty = trade_volumes[i] if i < len(trade_volumes) else "Không có tổng khối lượng giao dịch"
                
                print(f"Mã chứng khoán: {stock_code}, Giá trần: {ceiling_price}, Giá sàn: {floor_price}, Giá tham chiếu: {tc_price}, Giá bán 1: {best1offer_price} ,Tổng KL giao dịch: {total_traded_qty}")
                result.append({
                    "stock_code": stock_code,
                    "ceiling_price": ceiling_price,
                    "floor_price": floor_price,
                    "tc_price": tc_price,
                    "best1offer_price": best1offer_price,
                    "total_traded_qty": total_traded_qty
                })  

            # Đóng trình duyệt
            browser.close()
            return result
        
    except Exception as e:
        print(f"Lỗi: {e}")

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

            #lấy giá bán 1
            best1offer_cells = page.locator("//div[contains(@class, 'ag-cell') and @col-id='best1Offer']").all()
            best1offer_price = best1offer_cells[index].inner_text().strip() if index < len(best1offer_cells) else "Không có giá bán 1"
           
            # Lấy danh sách tổng khối lượng giao dịch, bỏ qua "Tổng KL"
            trade_volume_elements = page.locator("//div[contains(@class, 'ag-cell') and @col-id='nmTotalTradedQty']").all()
            trade_volume = trade_volume_elements[index].inner_text().strip() if index < len(trade_volume_elements) else "Không có tổng khối lượng giao dịch"

            # In ra thông tin mã chứng khoán
            print(f"Mã chứng khoán: {stock_code}, Giá trần: {ceiling_price}, Giá sàn: {floor_price}, Giá tham chiếu: {tc_price},Giá bán 1: {best1offer_price} , Tổng KL giao dịch: {trade_volume}")

            # Đóng trình duyệt
            browser.close()

            return {
                "stock_code": stock_code,
                "ceiling_price": ceiling_price,
                "floor_price": floor_price,
                "tc_price": tc_price,
                "best1offer_price": best1offer_price,
                "total_traded_qty": trade_volume
            }

    except Exception as e:
        print(f"Lỗi: {e}")
        return None

if __name__ == "__main__":
    fetch_all_stock_data()
    # Gọi hàm fetch_single_stock_data với mã chứng khoán cụ thể
    single_stock_data = fetch_single_stock_data("SHB")  # Thay "ACB" bằng mã chứng khoán bạn muốn