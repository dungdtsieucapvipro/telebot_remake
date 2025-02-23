from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import asyncio
from get_stock_sql import fetch_all_stock_data, fetch_single_stock_data

# Tạo một thread pool để chạy các hàm đồng bộ trong môi trường bất đồng bộ
executor = ThreadPoolExecutor(max_workers=5)

# Hàm hiển thị danh sách các lệnh
async def display_help(update: Update) -> None:
    help_text = (
        "💡 *Hướng dẫn sử dụng bot:*\n"
        "- /hello: Chào hỏi bot\n"
        "- /getstock <Mã chứng khoán>: Xem thông tin về mã chứng khoán cụ thể (Ví dụ: `/getstock ACB`)\n"
        "- /getallstocks: Lấy tất cả thông tin chứng khoán hiện tại\n"
        "- /help: Hiển thị danh sách các lệnh\n"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

# Hàm chào hỏi
async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Hello {update.effective_user.first_name}!")
    await display_help(update)    

# Hàm lấy thông tin chứng khoán cụ thể
async def get_stock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        stock_code = context.args[0].strip().upper()
        await update.message.reply_text("Đang lấy dữ liệu, vui lòng đợi...")
        try:
            loop = asyncio.get_event_loop()
            stock_data = await loop.run_in_executor(executor, fetch_single_stock_data, stock_code)

            # Kiểm tra xem stock_data có phải là None không
            if stock_data is None:
                await update.message.reply_text("Không tìm thấy mã chứng khoán.")
                return

            # Kiểm tra xem stock_data có phải là một từ điển không
            if isinstance(stock_data, dict):
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                message = (
                    f"*Kết quả được lấy lúc:* `{current_time}`\n"
                    f"```\n"
                    f"| Mã chứng khoán | Giá trần  | Giá sàn  | Giá TC   | Tong Kl giao dịch |\n"
                    f"|----------------|-----------|----------|----------|-------------------|\n"
                    f"| {stock_data['stock_code']:<14} | {stock_data['ceiling_price']:<9} | {stock_data['floor_price']:<8} | {stock_data['tc_price']:<8} | {stock_data['total_traded_qty']:<12} |\n"
                    f"```"
                )
                await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text("Không tìm thấy mã chứng khoán.")
        except Exception as e:
            await update.message.reply_text(f"Đã xảy ra lỗi: {str(e)}")
    else:
        await update.message.reply_text(
            "Vui lòng nhập mã chứng khoán sau lệnh /getstock. Ví dụ: /getstock ACB"
        )
    await display_help(update)

# Hàm lấy tất cả thông tin chứng khoán
async def get_all_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Đang lấy dữ liệu, vui lòng đợi...")
    try:
        loop = asyncio.get_event_loop()
        stock_data = await loop.run_in_executor(executor, fetch_all_stock_data)
        if stock_data:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            header = (
                f"*Kết quả được lấy lúc:* `{current_time}`\n"
                f"```\n"
                f"| Mã chứng khoán | Giá trần  | Giá sàn  | Giá TC   | Tong Kl giao dịch |\n"
                f"|----------------|-----------|----------|----------|-------------------|\n"
            )
            rows = ""
            for item in stock_data:
                rows += (
                    f"| {item['stock_code']:<14} | {item['ceiling_price']:<9} | {item['floor_price']:<8} | {item['tc_price']:<8} | {item['total_traded_qty']:<12} |\n"
                )
            footer = "```"
            message = header + rows + footer
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("Không tìm thấy dữ liệu chứng khoán.")
    except Exception as e:
        await update.message.reply_text(f"Đã xảy ra lỗi: {str(e)}")
    await display_help(update)

# Lệnh /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await display_help(update)    

# Khởi tạo bot
app = ApplicationBuilder().token('7928962019:AAFT_w5aEzE-M875p1zPkJTSn7r1a7tLRNY').build()

# Thêm các lệnh
app.add_handler(CommandHandler("hello", hello))
app.add_handler(CommandHandler("getstock", get_stock))
app.add_handler(CommandHandler("getallstocks", get_all_stocks))
app.add_handler(CommandHandler("help", help_command))

# Chạy bot
app.run_polling()
