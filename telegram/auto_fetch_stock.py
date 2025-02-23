from get_stock_sql import fetch_all_stock_data
import time



def countdown(t):
    """Hàm đếm ngược thời gian từ 60 giây xuống 0."""
    while t:
        mins, secs = divmod(t, 60)
        timer = '{:02d}'.format(secs)
        print(f"\rChuẩn bị lấy dữ liệu sau: {timer} giây", end="")
        time.sleep(1)
        t -= 1

    print("\rĐếm ngược: 00:00")

def main():
    
    while True:
        try:
            
            fetch_all_stock_data()  # Gọi hàm để lấy dữ liệu
            countdown(60)  # Đếm ngược 60 giây
            
        except Exception as e:
            time.sleep(60)  # Đợi 1 phút trước khi thử lại

if __name__ == "__main__":
    main() 