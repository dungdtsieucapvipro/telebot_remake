from telegram import Update, BotCommand
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, JobQueue
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import asyncio
from get_stock_sql import fetch_all_stock_data, fetch_single_stock_data, single_stock_data, all_stock_data
import logging  # Thêm import logging
from sql.database import connect_database
import logging 
from user_events import log_user_event
import mysql.connector


#! Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


#! Tạo một thread pool để chạy các hàm đồng bộ trong môi trường bất đồng bộ
executor = ThreadPoolExecutor(max_workers=5)


#! Hàm hiển thị danh sách các lệnh
async def display_help(update: Update) -> None:
    help_text = (
        "💡 *Hướng dẫn sử dụng bot:*\n"
        "- /hello: Chào hỏi bot\n"
        "- /getstock <Mã chứng khoán>: Xem thông tin về mã chứng khoán cụ thể (Ví dụ: `/getstock ACB`)\n"
        "- /getallstocks: Lấy tất cả thông tin chứng khoán hiện tại\n"
        "- /theodoi3p: Theo dõi giá 1 của mã chứng khoán trong 3 phút (Ví dụ: `/theodoi3p ACB`)\n"
        "- /theodoiall <Số phút>: Theo dõi giá 1 của tất cả mã chứng khoán trong khoảng thời gian đã chỉ định, nếu tăng 1% thì sẽ thông baó (Ví dụ: `/theodoiall 5`)\n"
        "- /batdauchoidoi <Mã chứng khoán> <Điều kiện> <Giá>: Theo dõi giá 1 của mã chứng khoán và thông báo khi điều kiện được thỏa mãn (Ví dụ: `/batdauchoidoi ACB > 25.00`)\n"
        "- /dungchodoi: Dừng theo dõi điều kiện đã đặt cho mã chứng khoán (Ví dụ: `/dungchodoi`)\n"
        "- /xemlog: Xem nhật ký sự kiện của bạn (hoặc tất cả nếu bạn là admin)\n"
        "- /help: Hiển thị danh sách các lệnh này\n"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

#! Hàm thiết lập các lệnh cho bot
async def set_bot_commands(application):
    commands = [
        BotCommand("hello", "Chào hỏi bot"),
        BotCommand("auto", "Bắt đầu chế độ tự động lấy dữ liệu"),
        BotCommand("stop", "Dừng chế độ tự động lấy dữ liệu"),
        BotCommand("getstock", "Lấy thông tin mã chứng khoán"),
        BotCommand("getallstocks", "Lấy tất cả thông tin chứng khoán"),
        BotCommand("theodoi3p", "Theo dõi mã ck trong 3p (Ví dụ: `/theodoi3p ACB`)"),
        BotCommand("help", "Hướng dẫn sử dụng bot"),
    ]
    await application.bot.set_my_commands(commands)

#! Hàm chào hỏi
# Example command handler with logging
async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username
    command = "hello"
    details = "User greeted the bot"
    chat_id = update.effective_chat.id

    # Log the user event
    log_user_event(user_id, username, command, details, chat_id)

    await update.message.reply_text(f"Hello {update.effective_user.first_name}!") 


#! Lệnh /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await display_help(update)    


# Đặt ID của admin
ADMIN_ID = 6133213893  # Thay thế bằng ID của bạn

#! Hàm tự động lấy dữ liệu mỗi 1 phút
async def auto_fetch_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    command = "auto"
    details = "Started auto-fetching data"
    chat_id = update.effective_chat.id

    # Log the user event
    log_user_event(user_id, username, command, details, chat_id)

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    job = context.job_queue.run_repeating(fetch_data_job, interval=60, first=0, chat_id=update.message.chat_id)
    context.chat_data["auto_fetch_job"] = job
    await update.message.reply_text("Đã bắt đầu chế độ tự động lấy dữ liệu.")
    await display_help(update)

async def fetch_data_job(context: ContextTypes.DEFAULT_TYPE):
    await asyncio.get_event_loop().run_in_executor(executor, fetch_all_stock_data)
    logging.info("Đã tự động lấy dữ liệu chứng khoán.")

#! Hàm dừng chế độ tự động
async def stop_auto_fetch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    command = "stop"
    details = "Stopped auto-fetching data"
    chat_id = update.effective_chat.id

    # Log the user event
    log_user_event(user_id, username, command, details, chat_id)

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Bạn không có quyền sử dụng lệnh này.")
        return

    job = context.chat_data.get("auto_fetch_job")
    if job:
        job.schedule_removal()
        del context.chat_data["auto_fetch_job"]
        await update.message.reply_text("Đã dừng chế độ tự động.")
    else:
        await update.message.reply_text("Không có chế độ tự động nào đang chạy.")
    await display_help(update)

#! Hàm lấy thông tin chứng khoán cụ thể
async def get_stock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username
    command = "getstock"
    details = f"Requested stock info for {context.args[0]}" if context.args else "No stock code provided"
    chat_id = update.effective_chat.id

    # Log the user event
    log_user_event(user_id, username, command, details, chat_id)

    if context.args:
        stock_code = context.args[0].strip().upper()
        await update.message.reply_text("🔄 Đang lấy dữ liệu từ cơ sở dữ liệu, vui lòng đợi...")
        try:
            loop = asyncio.get_event_loop()
            stock_data_list = await loop.run_in_executor(executor, single_stock_data, stock_code)

            if stock_data_list and len(stock_data_list) > 0:
                stock_data = stock_data_list[0]
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                message = (
                    f"*Kết quả được lấy lúc:* `{current_time}`\n"
                    f"```\n"
                    f"| Mã chứng khoán | Giá trần  | Giá sàn  | Giá TC   | Giá Bán 1   |\n"
                    f"|----------------|-----------|----------|----------|----------|\n"
                    f"| {stock_data['stock_code']:<14} | {stock_data['ceiling_price']:<9} | {stock_data['floor_price']:<8} | {stock_data['tc_price']:<8} | {stock_data['best1offer_price']:<8} |\n"
                    f"```"
                )
                await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text("Không tìm thấy mã chứng khoán.")
        except Exception as e:
            logging.error(f"Đã xảy ra lỗi: {str(e)}")
            await update.message.reply_text(f"Đã xảy ra lỗi: {str(e)}")
    else:
        await update.message.reply_text("Vui lòng nhập mã chứng khoán sau lệnh /getstock. Ví dụ: /getstock ACB")
    await display_help(update)

#! Hàm lấy tất cả thông tin chứng khoán
async def get_all_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username
    command = "getallstocks"
    details = "Requested all stock info"
    chat_id = update.effective_chat.id

    # Log the user event
    log_user_event(user_id, username, command, details, chat_id)

    await update.message.reply_text("Đang lấy dữ liệu, vui lòng đợi...")
    try:
        loop = asyncio.get_event_loop()
        stock_data = await loop.run_in_executor(executor, all_stock_data)
        if stock_data:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            header = (
                f"*Kết quả được lấy lúc:* `{current_time}`\n"
                f"```\n"
                f"| Mã chứng khoán | Giá trần  | Giá sàn  | Giá TC   | Giá Bán 1   |\n"
                f"|----------------|-----------|----------|----------|----------|\n"
            )
            rows = ""
            for item in stock_data:
                rows += (
                    f"| {item['stock_code']:<14} | {item['ceiling_price']:<9} | {item['floor_price']:<8} | {item['tc_price']:<8} | {item['best1offer_price']:<8} |\n"
                )
            footer = "```"
            message = header + rows + footer
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("Không tìm thấy dữ liệu chứng khoán.")
    except Exception as e:
        logging.error(f"Đã xảy ra lỗi: {str(e)}")
        await update.message.reply_text(f"Đã xảy ra lỗi: {str(e)}")
    await display_help(update)

#! Hàm theo dõi giá trị bestOffer1
async def track_stock_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username
    command = "theodoi3p"
    details = f"Tracking stock price for {context.args[0]}" if context.args else "No stock code provided"
    chat_id = update.effective_chat.id

    # Log the user event
    log_user_event(user_id, username, command, details, chat_id)

    if context.args:
        stock_code = context.args[0].strip().upper()
        await update.message.reply_text(f"🔄 Đang theo dõi giá cho mã chứng khoán: {stock_code}...")

        # Lấy giá ban đầu từ cơ sở dữ liệu
        initial_data = await asyncio.get_event_loop().run_in_executor(executor, single_stock_data, stock_code)
        
        if not initial_data or len(initial_data) == 0:
            await update.message.reply_text("Không tìm thấy mã chứng khoán.")
            return
        
        # Truy cập phần tử đầu tiên trong danh sách
        initial_price = float(initial_data[0]['best1offer_price'])
        await asyncio.sleep(180)  # Chờ 3 phút

        # Lấy giá sau 3 phút
        updated_data = await asyncio.get_event_loop().run_in_executor(executor, single_stock_data, stock_code)
        
        if not updated_data or len(updated_data) == 0:
            await update.message.reply_text("Không tìm thấy mã chứng khoán.")
            return
        
        # Truy cập phần tử đầu tiên trong danh sách
        updated_price = float(updated_data[0]['best1offer_price'])

        # So sánh giá và thông báo
        if updated_price > initial_price:
            await update.message.reply_text(f"{stock_code} tăng từ {initial_price} lên {updated_price} → {stock_code} đáng đầu tư.")
        else:
            await update.message.reply_text(f"{stock_code} không đáng đầu tư.")
    else:
        await update.message.reply_text("Vui lòng nhập mã chứng khoán sau lệnh /theodoi3p. Ví dụ: /theodoi3p ACB")

#! Hàm theo dõi giá cho tất cả mã chứng khoán
async def track_all_stocks_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username
    command = "theodoiall"
    details = f"Tracking all stocks for {context.args[0]} minutes" if context.args else "No duration provided"
    chat_id = update.effective_chat.id

    # Log the user event
    log_user_event(user_id, username, command, details, chat_id)

    if context.args:
        try:
            duration_minutes = int(context.args[0])
            await update.message.reply_text(f"🔄 Đang theo dõi giá cho tất cả mã chứng khoán trong {duration_minutes} phút...")
            
            # Lấy tất cả mã chứng khoán
            all_stocks_data = await asyncio.get_event_loop().run_in_executor(executor, all_stock_data)
            initial_prices = {item['stock_code']: float(item['best1offer_price']) for item in all_stocks_data}
            await asyncio.sleep(duration_minutes * 60)  # Chờ trong thời gian đã nhập

            # Lấy giá sau thời gian theo dõi
            updated_stocks_data = await asyncio.get_event_loop().run_in_executor(executor, all_stock_data)
            updated_prices = {item['stock_code']: float(item['best1offer_price']) for item in updated_stocks_data}

            # So sánh giá và thông báo
            increased_stocks = []
            max_increase = 0
            best_stock = None

            for stock_code, initial_price in initial_prices.items():
                updated_price = updated_prices.get(stock_code)
                if updated_price:
                    increase_percentage = ((updated_price - initial_price) / initial_price) * 100
                    if increase_percentage >= 1:  # Nếu tăng từ 1%
                        increased_stocks.append((stock_code, initial_price, updated_price, increase_percentage))
                        if increase_percentage > max_increase:
                            max_increase = increase_percentage
                            best_stock = (stock_code, initial_price, updated_price)

            # Gửi thông báo
            if increased_stocks:
                for stock in increased_stocks:
                    await update.message.reply_text(f"{stock[0]} tăng từ {stock[1]} lên {stock[2]} ({stock[3]:.2f}%)")
                if best_stock:
                    await update.message.reply_text(f"{best_stock[0]} là mã chứng khoán đáng đầu tư nhất, tăng từ {best_stock[1]} lên {best_stock[2]} ({max_increase:.2f}%)")
            else:
                await update.message.reply_text("Không có mã chứng khoán nào tăng từ 1% trở lên.")
        except ValueError:
            await update.message.reply_text("Vui lòng nhập số phút hợp lệ.")
    else:
        await update.message.reply_text("Vui lòng nhập số phút theo dõi sau lệnh /theodoiall. Ví dụ: /theodoiall 5")

#! Hàm bắt đầu chờ đợi điều kiện
async def start_waiting_for_condition(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username
    command = "batdauchoidoi"
    details = f"Started waiting for condition on {context.args[0]}" if context.args else "No stock code provided"
    chat_id = update.effective_chat.id

    # Log the user event
    log_user_event(user_id, username, command, details, chat_id)

    if context.args and len(context.args) == 3:
        stock_code = context.args[0].strip().upper()
        comparison_operator = context.args[1].strip()  # ">" hoặc "<"
        target_price = float(context.args[2])

        await update.message.reply_text(f"🔄 Đang theo dõi giá cho mã chứng khoán: {stock_code}...")

        # Lưu job vào context để có thể hủy sau này
        job = context.job_queue.run_repeating(check_stock_price, interval=10, first=0, context=(update.message.chat_id, stock_code, comparison_operator, target_price))
        context.chat_data["waiting_job"] = job
        await update.message.reply_text("Đã bắt đầu theo dõi điều kiện.")

    else:
        await update.message.reply_text("Vui lòng nhập mã chứng khoán, điều kiện so sánh và giá. Ví dụ: /batdauchoidoi ACB > 25.00")

#! Hàm kiểm tra giá chứng khoán
async def check_stock_price(context: ContextTypes.DEFAULT_TYPE):
    chat_id, stock_code, comparison_operator, target_price = context.job.context

    # Lấy giá hiện tại từ cơ sở dữ liệu
    stock_data = await asyncio.get_event_loop().run_in_executor(executor, single_stock_data, stock_code)

    if not stock_data or len(stock_data) == 0:
        await context.bot.send_message(chat_id, f"Không tìm thấy mã chứng khoán {stock_code}.")
        return

    current_price = float(stock_data[0]['best1offer_price'])

    # So sánh giá
    if comparison_operator == ">":
        if current_price > target_price:
            await context.bot.send_message(chat_id, f"{stock_code} hiện tại có giá {current_price}, lớn hơn {target_price}.")
            context.job.schedule_removal()  # Hủy job
    elif comparison_operator == "<":
        if current_price < target_price:
            await context.bot.send_message(chat_id, f"{stock_code} hiện tại có giá {current_price}, nhỏ hơn {target_price}.")
            context.job.schedule_removal()  # Hủy job

#! Hàm dừng theo dõi điều kiện
async def stop_waiting_for_condition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    command = "dungchodoi"
    details = "Stopped waiting for condition"
    chat_id = update.effective_chat.id

    # Log the user event
    log_user_event(user_id, username, command, details, chat_id)

    job = context.chat_data.get("waiting_job")
    if job:
        job.schedule_removal()
        del context.chat_data["waiting_job"]
        await update.message.reply_text("Đã dừng theo dõi điều kiện.")
    else:
        await update.message.reply_text("Không có lệnh nào đang chạy.")

#! Hàm xem log người dùng
async def view_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username
    command = "xemlog"
    details = "Viewed logs"
    chat_id = update.effective_chat.id

    # Log the user event
    log_user_event(user_id, username, command, details, chat_id)

    connection = connect_database()
    if connection is None:
        await update.message.reply_text("Không thể kết nối đến cơ sở dữ liệu.")
        return

    try:
        cursor = connection.cursor(dictionary=True)
        if user_id == ADMIN_ID:
            query = "SELECT * FROM user_events ORDER BY timestamp DESC LIMIT 10"
            cursor.execute(query)
        else:
            query = "SELECT * FROM user_events WHERE user_id = %s ORDER BY timestamp DESC LIMIT 10"
            cursor.execute(query, (user_id,))

        logs = cursor.fetchall()
        if logs:
            message = "*Nhật ký sự kiện gần đây:*\n"
            for log in logs:
                message += (
                    f"- User: {log['username']}\n"
                    f"  Command: {log['command']}\n"
                    f"  Details: {log['details']}\n"
                    f"  Time: {log['timestamp']}\n"
                    f"  Chat ID: {log['chat_id']}\n"
                    "\n"
                )
            # Log the message to check its content
            logging.info(f"Sending message: {message}")
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("Không có nhật ký nào để hiển thị.")
    except mysql.connector.Error as err:
        logging.error(f"Đã xảy ra lỗi khi truy vấn nhật ký: {err}")
        await update.message.reply_text("Đã xảy ra lỗi khi truy vấn nhật ký.")
    finally:
        cursor.close()
        connection.close()

#! Khởi tạo bot
app = ApplicationBuilder().token('7928962019:AAFT_w5aEzE-M875p1zPkJTSn7r1a7tLRNY').build()

#! Thêm các lệnh
app.add_handler(CommandHandler("hello", hello))
app.add_handler(CommandHandler("getstock", get_stock))
app.add_handler(CommandHandler("getallstocks", get_all_stocks))
app.add_handler(CommandHandler("auto", auto_fetch_data))
app.add_handler(CommandHandler("stop", stop_auto_fetch))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("theodoi3p", track_stock_price))
app.add_handler(CommandHandler("theodoiall", track_all_stocks_price))
app.add_handler(CommandHandler("batdauchoidoi", start_waiting_for_condition))
app.add_handler(CommandHandler("dungchodoi", stop_waiting_for_condition))
app.add_handler(CommandHandler("xemlog", view_logs))

#! Chạy bot
app.run_polling()