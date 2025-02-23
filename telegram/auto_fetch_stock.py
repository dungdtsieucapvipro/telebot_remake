import logging
from get_stock_sql import fetch_all_stock_data
import time

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def count_down(t):
    # Hàm đếm ngược thời gian từ 60 giây xuống 0.
    while t:
        mins, secs = divmod(t, 60)
        timer = '{:02d}'.format(secs)
        print(f"\rChuẩn bị lấy dữ liệu sau: {timer} giây", end="")
        time.sleep(1)
        t -= 1

    print("\rĐếm ngược: 00:00")

def auto_fetch_stock():
    logging.info("Bắt đầu hệ thống lấy dữ liệu tự động")
    
    while True:
        try:
            logging.info("Chuẩn bị lấy dữ liệu...")
            
            fetch_all_stock_data()  # Gọi hàm để lấy dữ liệu
            count_down(60)  # Đếm ngược 60 giây
            logging.info("Đã lấy và lưu dữ liệu thành công.")
            
        except Exception as e:
            logging.error(f"Lỗi khi lấy dữ liệu: {str(e)}")
            time.sleep(60)  # Đợi 1 phút trước khi thử lại

if __name__ == "__main__":
    auto_fetch_stock() 