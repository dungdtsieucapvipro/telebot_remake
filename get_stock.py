import time
from playwright.sync_api import sync_playwright

def scroll_down(page, scroll_element_selector, step=50, max_height=300):
    scroll_position = 0
    while scroll_position < max_height:
        page.eval_on_selector(scroll_element_selector, f"el => el.scrollTop = {scroll_position}")
        scroll_position += step
        time.sleep(0.5)

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
    stock_codes = list(map(lambda el: el.inner_text().strip(), stock_code_elements.all()))
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

    # Lấy danh sách tổng khối lượng giao dịch, bỏ qua "Tổng KL"
    trade_volume_elements = page.locator("//div[contains(@class, 'ag-cell') and @col-id='nmTotalTradedQty']").all()
    trade_volumes = []
    for volume in trade_volume_elements:
        trade_volume = volume.inner_text().strip()
        if trade_volume != "Tổng KL" and trade_volume != "":
            trade_volumes.append(trade_volume)

    # In ra mã chứng khoán kèm giá trần, giá sàn và giá tham chiếu và tổng khối lượng giao dịch
    for i in range(len(stock_codes)):
        stock_code = stock_codes[i]
        ceiling_price = ceiling_prices[i] if i < len(ceiling_prices) else "Không có giá trần"
        floor_price = floor_prices[i] if i < len(floor_prices) else "Không có giá sàn"
        tc_price = tc_prices[i] if i < len(tc_prices) else "Không có giá tham chiếu"
        total_traded_qty = trade_volumes[i] if i < len(trade_volumes) else "Không có tổng khối lượng giao dịch"
        print(f"Mã chứng khoán: {stock_code}, Giá trần: {ceiling_price}, Giá sàn: {floor_price}, Giá tham chiếu: {tc_price}, Tổng KL giao dịch: {total_traded_qty}")

    # Đóng trình duyệt
    browser.close()
