import tkinter as tk
from tkinter import ttk, messagebox
import pymysql
from pymysql import OperationalError
import datetime
class Database:
    def __init__(self):
        self.config = {
            "host": "localhost",
            "user": "root",
            "password": "zcy123456", 
            "database": "restaurant_db",
            "cursorclass": pymysql.cursors.DictCursor
        }
        self.connect()
        
    def connect(self):
        try:
            self.conn = pymysql.connect(**self.config)
        except OperationalError as e:
            messagebox.showerror("数据库连接失败", f"请检查配置: {str(e)}")
            raise

    def query(self, sql, params=None):
        with self.conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()

    def execute(self, sql, params=None):
        with self.conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            self.conn.commit()

class CustomerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("膳食阁-食客点餐")
        self.root.geometry("1000x600")
        self.db = Database()
        self.current_table_id = 1
        self.selected_items = []
        self.cart_buttons = {}
        self.current_order_id = None

        self.create_widgets()
        self.load_menu_items()

    def create_widgets(self):
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(top_frame, text="选择桌号:").pack(side=tk.LEFT, padx=5)

        self.table_var = tk.StringVar(value="1")
        table_combo = ttk.Combobox(top_frame, textvariable=self.table_var, values=[str(i) for i in range(1, 21)],
                                   width=5)
        table_combo.pack(side=tk.LEFT, padx=5)
        table_combo.bind("<<ComboboxSelected>>", self.update_table_id)

        self.order_info_lbl = ttk.Label(top_frame, text="订单: 未生成")
        self.order_info_lbl.pack(side=tk.RIGHT, padx=20)

        middle_frame = ttk.Frame(self.root)
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        ttk.Label(middle_frame, text="菜单", font=("微软雅黑", 12, "bold")).pack(pady=5)
        self.menu_frame = ttk.Frame(middle_frame)
        self.menu_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        ttk.Label(middle_frame, text="购物车", font=("微软雅黑", 12, "bold")).pack(pady=5)
        self.cart_frame = ttk.Frame(middle_frame)
        self.cart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)

        self.submit_btn = ttk.Button(bottom_frame, text="提交订单", command=self.submit_order, state=tk.DISABLED)
        self.submit_btn.pack(side=tk.RIGHT, padx=10)

    def update_table_id(self, event):
        try:
            self.current_table_id = int(self.table_var.get())
        except ValueError:
            self.current_table_id = 1
            self.table_var.set("1")

    def load_menu_items(self):
        for widget in self.menu_frame.winfo_children():
            widget.destroy()

        columns = ("id", "name", "price", "profit", "desc", "add")
        self.menu_tree = ttk.Treeview(self.menu_frame, columns=columns, show="headings")

        self.menu_tree.heading("id", text="ID")
        self.menu_tree.heading("name", text="名称")
        self.menu_tree.heading("price", text="价格")
        self.menu_tree.heading("profit", text="利润")
        self.menu_tree.heading("desc", text="描述")
        self.menu_tree.heading("add", text="操作")

        self.menu_tree.column("id", width=50, anchor=tk.CENTER)
        self.menu_tree.column("name", width=120, anchor=tk.CENTER)
        self.menu_tree.column("price", width=80, anchor=tk.CENTER)
        self.menu_tree.column("profit", width=80, anchor=tk.CENTER)
        self.menu_tree.column("desc", width=200, anchor=tk.W)
        self.menu_tree.column("add", width=80, anchor=tk.CENTER)

        self.menu_tree.pack(fill=tk.BOTH, expand=True)
        self.menu_tree.bind("<ButtonRelease-1>", self.on_menu_click)

        menu_data = self.db.query("SELECT * FROM menu")
        for item in menu_data:
            self.menu_tree.insert("", tk.END, values=(
                item["dish_id"],
                item["dish_name"],
                f"{item['price']}元",
                f"{item['profit_per_dish']}元",
                item["description"],
                "添加"
            ))

    def on_menu_click(self, event):
        region = self.menu_tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        item = self.menu_tree.selection()[0]
        column = int(self.menu_tree.identify_column(event.x).replace('#', ''))

        if column == 6:  
            dish_id = self.menu_tree.item(item, "values")[0]
            self.add_to_cart(dish_id)

    def add_to_cart(self, dish_id):
        menu_item = next((item for item in self.db.query("SELECT * FROM menu WHERE dish_id = %s", (dish_id,))), None)
        if not menu_item:
            return

        existing_item = next((item for item in self.selected_items if item["dish_id"] == dish_id), None)

        if existing_item:
            existing_item["quantity"] += 1
        else:
            self.selected_items.append({
                "dish_id": dish_id,
                "dish_name": menu_item["dish_name"],
                "price": menu_item["price"],
                "quantity": 1
            })

        self.update_cart()
        self.submit_btn.config(state=tk.NORMAL if self.selected_items else tk.DISABLED)

    def update_cart(self):
        for widget in self.cart_frame.winfo_children():
            widget.destroy()

        if not self.selected_items:
            ttk.Label(self.cart_frame, text="购物车为空").pack(pady=20)
            return

        cart_columns = ("name", "price", "quantity", "subtotal", "action")
        cart_tree = ttk.Treeview(self.cart_frame, columns=cart_columns, show="headings")

        cart_tree.heading("name", text="名称")
        cart_tree.heading("price", text="单价")
        cart_tree.heading("quantity", text="数量")
        cart_tree.heading("subtotal", text="小计")
        cart_tree.heading("action", text="操作")

        cart_tree.column("name", width=120, anchor=tk.CENTER)
        cart_tree.column("price", width=80, anchor=tk.CENTER)
        cart_tree.column("quantity", width=80, anchor=tk.CENTER)
        cart_tree.column("subtotal", width=80, anchor=tk.CENTER)
        cart_tree.column("action", width=120, anchor=tk.CENTER)

        cart_tree.pack(fill=tk.BOTH, expand=True)

        for item in self.selected_items:
            subtotal = item["price"] * item["quantity"]
            cart_tree.insert("", tk.END, values=(
                item["dish_name"],
                f"{item['price']}元",
                item["quantity"],
                f"{subtotal}元",
                f"修改"
            ))

        total = sum(item["price"] * item["quantity"] for item in self.selected_items)
        ttk.Label(self.cart_frame, text=f"总价: {total}元", font=("微软雅黑", 12, "bold")).pack(pady=10)

    def decrease_quantity(self, dish_id):
        item = next((item for item in self.selected_items if item["dish_id"] == dish_id), None)
        if item:
            if item["quantity"] > 1:
                item["quantity"] -= 1
            else:
                self.selected_items.remove(item)
            self.update_cart()
            self.submit_btn.config(state=tk.NORMAL if self.selected_items else tk.DISABLED)

    def increase_quantity(self, dish_id):
        item = next((item for item in self.selected_items if item["dish_id"] == dish_id), None)
        if item:
            item["quantity"] += 1
            self.update_cart()

    def generate_order_id(self):
        try:
            today = datetime.date.today()
            date_str = today.strftime("%Y%m%d")

            sql = """
            SELECT MAX(SUBSTRING(order_id, 9, 4)) AS max_seq 
            FROM orders 
            WHERE create_date = %s
            """
            result = self.db.query(sql, (today,))
            max_seq = result[0]["max_seq"] if result and result[0]["max_seq"] else "0000"

            new_seq = int(max_seq) + 1

            seq_str = f"{new_seq:04d}"

            return f"{date_str}{seq_str}"

        except Exception as e:
            messagebox.showerror("错误", f"生成订单号失败: {str(e)}")
            return None

    def submit_order(self):
        if not self.selected_items:
            messagebox.showinfo("提示", "购物车为空")
            return

        if not self.current_table_id or self.current_table_id < 1 or self.current_table_id > 20:
            messagebox.showerror("错误", "请选择有效桌号（1-20）")
            return

        try:
            order_id = self.generate_order_id()
            if not order_id:
                return

            self.db.execute("START TRANSACTION")

            for item in self.selected_items:
                subtotal = item["price"] * item["quantity"]
                self.db.execute(
                    """INSERT INTO orders (order_id, table_id, dish_id, quantity, subtotal, order_time, create_date)
                       VALUES (%s, %s, %s, %s, %s, NOW(), CURDATE())""",
                    (order_id, self.current_table_id, item["dish_id"], item["quantity"], subtotal)
                )

            self.db.execute("COMMIT")

            self.current_order_id = order_id
            self.order_info_lbl.config(text=f"订单: {order_id}")

            total_amount = sum(item["price"] * item["quantity"] for item in self.selected_items)
            messagebox.showinfo(
                "订单提交成功",
                f"桌号 {self.current_table_id}\n"
                f"订单号: {order_id}\n"
                f"共 {len(self.selected_items)} 种菜品\n"
                f"总价: {total_amount:.2f} 元\n\n"
                "订单已提交至后厨！"
            )

            self.selected_items = []
            self.update_cart()
            self.submit_btn.config(state=tk.DISABLED)

        except Exception as e:
            self.db.execute("ROLLBACK")
            messagebox.showerror("错误", f"订单提交失败: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CustomerApp(root)
    root.mainloop()
