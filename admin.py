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
class AdminApp:
    def __init__(self, root):
        self.root = root
        self.root.title("膳食阁-管理员界面")
        self.root.geometry("1200x600")
        self.db = Database()

        self.create_status_bar()
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.init_menu_tab()
        self.init_sales_tab()
        self.init_profit_tab()
        self.init_orders_tab()

        self.update_clock()

    def create_status_bar(self):
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Label(status_frame, text="当前用户: 管理员", padding=(5, 2)).pack(side=tk.LEFT)
        self.time_label = ttk.Label(status_frame, text="", padding=(5, 2))
        self.time_label.pack(side=tk.RIGHT)

    def update_clock(self):
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_clock)

    def init_menu_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="菜单管理")

        ttk.Label(tab, text="菜品管理", font=("微软雅黑", 14), background="#4a7abc", foreground="white").pack(pady=10,fill=tk.X,padx=10)

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(pady=5, fill=tk.X)
        ttk.Button(btn_frame, text="添加菜品", command=self.add_dish).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="刷新", command=self.load_menu).pack(side=tk.LEFT, padx=5)

        search_frame = ttk.Frame(tab)
        search_frame.pack(fill=tk.X, pady=5)
        ttk.Label(search_frame, text="搜索菜品:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="搜索", command=self.search_dishes).pack(side=tk.LEFT, padx=5)

        self.menu_tree = ttk.Treeview(tab, columns=("id", "name", "price", "profit", "desc", "edit", "delete"),show="headings")
        self.menu_tree.heading("id", text="ID")
        self.menu_tree.heading("name", text="名称")
        self.menu_tree.heading("price", text="价格")
        self.menu_tree.heading("profit", text="单份利润")
        self.menu_tree.heading("desc", text="描述")
        self.menu_tree.heading("edit", text="编辑")
        self.menu_tree.heading("delete", text="删除")

        self.menu_tree.column("id", width=50, anchor=tk.CENTER)
        self.menu_tree.column("name", width=150, anchor=tk.CENTER)
        self.menu_tree.column("price", width=80, anchor=tk.CENTER)
        self.menu_tree.column("profit", width=80, anchor=tk.CENTER)
        self.menu_tree.column("desc", width=300, anchor=tk.W)
        self.menu_tree.column("edit", width=60, anchor=tk.CENTER)
        self.menu_tree.column("delete", width=60, anchor=tk.CENTER)

        self.menu_tree.pack(fill=tk.BOTH, expand=True)
        self.menu_tree.bind("<ButtonRelease-1>", self.on_menu_click)
        self.load_menu()

    def load_menu(self, keyword=None):
        self.menu_tree.delete(*self.menu_tree.get_children())
        query = "SELECT dish_id, dish_name, price, profit_per_dish, description FROM menu"
        params = ()
        if keyword:
            query += " WHERE dish_name LIKE %s"
            params = (f"%{keyword}%",)
        data = self.db.query(query, params)
        for row in data:
            self.menu_tree.insert("", tk.END, values=
            (
                row["dish_id"], row["dish_name"],
                f"{row['price']:.2f}元", f"{row['profit_per_dish']:.2f}元",
                row["description"], "编辑", "删除"
            ))

    def search_dishes(self):
        keyword = self.search_entry.get().strip()
        self.load_menu(keyword if keyword else None)

    def on_menu_click(self, event):
        region = self.menu_tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        item = self.menu_tree.selection()[0]
        column = int(self.menu_tree.identify_column(event.x).replace('#', ''))
        dish_id = self.menu_tree.item(item, "values")[0]
        if column == 6:
            self.edit_dish(dish_id)
        elif column == 7:
            self.delete_dish(dish_id)

    def add_dish(self):
        win = tk.Toplevel(self.root)
        win.title("添加菜品")
        win.geometry("400x300")
        win.resizable(False, False)

        ttk.Label(win, text="菜品名称:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_entry = ttk.Entry(win, width=30)
        name_entry.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(win, text="价格(元):").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        price_entry = ttk.Entry(win, width=30)
        price_entry.grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(win, text="单份利润(元):").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        profit_entry = ttk.Entry(win, width=30)
        profit_entry.grid(row=2, column=1, padx=10, pady=10)

        ttk.Label(win, text="描述:").grid(row=3, column=0, padx=10, pady=10, sticky=tk.NW)
        desc_text = tk.Text(win, width=30, height=5)
        desc_text.grid(row=3, column=1, padx=10, pady=10)

        def save_dish():
            name = name_entry.get()
            price = price_entry.get()
            profit = profit_entry.get()
            desc = desc_text.get("1.0", tk.END).strip()

            if not name or not price or not profit:
                messagebox.showerror("错误", "请填写必填字段")
                return

            try:
                price = float(price)
                profit = float(profit)
            except ValueError:
                messagebox.showerror("错误", "价格和利润必须为数字")
                return

            try:
                self.db.execute(
                    "INSERT INTO menu (dish_name, price, profit_per_dish, description) VALUES (%s, %s, %s, %s)",
                    (name, price, profit, desc)
                )
                messagebox.showinfo("成功", "菜品添加成功")
                self.load_menu()
                win.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"添加失败: {str(e)}")

        ttk.Button(win, text="保存", command=save_dish).grid(row=4, column=0, padx=10, pady=10)
        ttk.Button(win, text="取消", command=win.destroy).grid(row=4, column=1, padx=10, pady=10)

    def edit_dish(self, dish_id):
        data = self.db.query("SELECT * FROM menu WHERE dish_id = %s", (dish_id,))[0]

        win = tk.Toplevel(self.root)
        win.title("编辑菜品")
        win.geometry("400x300")
        win.resizable(False, False)

        ttk.Label(win, text="菜品名称:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_entry = ttk.Entry(win, width=30)
        name_entry.insert(0, data["dish_name"])
        name_entry.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(win, text="价格(元):").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        price_entry = ttk.Entry(win, width=30)
        price_entry.insert(0, str(data["price"]))
        price_entry.grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(win, text="单份利润(元):").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        profit_entry = ttk.Entry(win, width=30)
        profit_entry.insert(0, str(data["profit_per_dish"]))
        profit_entry.grid(row=2, column=1, padx=10, pady=10)

        ttk.Label(win, text="描述:").grid(row=3, column=0, padx=10, pady=10, sticky=tk.NW)
        desc_text = tk.Text(win, width=30, height=5)
        desc_text.insert("1.0", data["description"])
        desc_text.grid(row=3, column=1, padx=10, pady=10)

        def update_dish():
            name = name_entry.get()
            price = price_entry.get()
            profit = profit_entry.get()
            desc = desc_text.get("1.0", tk.END).strip()

            if not name or not price or not profit:
                messagebox.showerror("错误", "请填写必填字段")
                return

            try:
                price = float(price)
                profit = float(profit)
            except ValueError:
                messagebox.showerror("错误", "价格和利润必须为数字")
                return

            try:
                self.db.execute(
                    "CALL update_menu_price(%s, %s)",
                    (dish_id, price)
                )

                self.db.execute(
                    """UPDATE menu 
                       SET dish_name = %s, profit_per_dish = %s, description = %s 
                       WHERE dish_id = %s""",
                    (name, profit, desc, dish_id)
                )

                messagebox.showinfo("成功", "菜品更新成功")
                self.load_menu()
                win.destroy()

            except pymysql.Error as e:
                if e.args[0] == 1644:
                    messagebox.showerror("价格错误", "价格必须大于0")
                else:
                    messagebox.showerror("错误", f"更新失败: {str(e)}")
                self.db.conn.rollback()

        ttk.Button(win, text="保存", command=update_dish).grid(row=4, column=0, padx=10, pady=10)
        ttk.Button(win, text="取消", command=win.destroy).grid(row=4, column=1, padx=10, pady=10)

    def delete_dish(self, dish_id):
        if messagebox.askyesno("确认删除", "确定要删除此菜品吗？"):
            try:
                self.db.execute("DELETE FROM menu WHERE dish_id = %s", (dish_id,))
                messagebox.showinfo("成功", "菜品已删除")
                self.load_menu()
            except Exception as e:
                messagebox.showerror("错误", f"删除失败: {str(e)}")

    def init_sales_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="销售统计")
        ttk.Label(tab, text="菜品销售统计", font=("微软雅黑", 14), background="#4a7abc", foreground="white").pack(
            pady=10, fill=tk.X, padx=10)

        filter_frame = ttk.Frame(tab)
        filter_frame.pack(fill=tk.X, pady=5)
        ttk.Button(filter_frame, text="按销量排序", command=lambda: self.load_sales("total_sales DESC")).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="按利润排序", command=lambda: self.load_sales("total_profit DESC")).pack(
            side=tk.LEFT, padx=5)

        self.sales_tree = ttk.Treeview(tab, columns=("id", "name", "sales", "revenue", "profit"), show="headings")
        self.sales_tree.heading("id", text="ID")
        self.sales_tree.heading("name", text="名称")
        self.sales_tree.heading("sales", text="总销量")
        self.sales_tree.heading("revenue", text="总收入")
        self.sales_tree.heading("profit", text="总利润")

        self.sales_tree.column("id", width=50, anchor=tk.CENTER)
        self.sales_tree.column("name", width=150, anchor=tk.CENTER)
        self.sales_tree.column("sales", width=100, anchor=tk.CENTER)
        self.sales_tree.column("revenue", width=120, anchor=tk.CENTER)
        self.sales_tree.column("profit", width=120, anchor=tk.CENTER)

        self.sales_tree.pack(fill=tk.BOTH, expand=True)
        self.load_sales()

    def load_sales(self, order_by="total_sales DESC"):
        self.sales_tree.delete(*self.sales_tree.get_children())
        sql = """
        SELECT 
            m.dish_id, 
            m.dish_name, 
            s.total_sales,
            s.total_revenue,
            s.total_profit
        FROM menu m 
        JOIN sales_statistics s ON m.dish_id = s.dish_id
        ORDER BY {order_by}
        """
        data = self.db.query(sql.format(order_by=order_by))
        for row in data:
            self.sales_tree.insert("", tk.END, values=(
                row["dish_id"],
                row["dish_name"],
                row["total_sales"],
                f"{row['total_revenue']:.2f}元",
                f"{row['total_profit']:.2f}元"
            ))

    def init_profit_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="总利润统计")
        ttk.Label(tab, text="餐厅总利润", font=("微软雅黑", 14), background="#4a7abc", foreground="white").pack(pady=10,fill=tk.X,padx=10)

        profit_frame = ttk.Frame(tab)
        profit_frame.pack(pady=20)
        ttk.Label(profit_frame, text="当前总利润:", font=("微软雅黑", 12)).pack(side=tk.LEFT, padx=10)
        self.profit_lbl = ttk.Label(profit_frame, text="0.00元", font=("微软雅黑", 18, "bold"))
        self.profit_lbl.pack(side=tk.LEFT, padx=10)

        ttk.Button(tab, text="刷新", command=self.refresh_profit).pack(pady=10)
        self.refresh_profit()

    def refresh_profit(self):
        data = self.db.query("SELECT total_profit FROM total_restaurant_profit")
        if data and data[0]['total_profit'] is not None:
            self.profit_lbl.config(text=f"{data[0]['total_profit']:.2f}元")
        else:
            self.profit_lbl.config(text="0.00元")

    def init_orders_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="订单管理")

        ttk.Label(tab, text="订单列表", font=("微软雅黑", 14), background="#4a7abc", foreground="white").pack(pady=10, fill=tk.X, padx=10)
        filter_frame = ttk.Frame(tab)
        filter_frame.pack(fill=tk.X, pady=5)
        ttk.Button(filter_frame, text="刷新", command=self.load_orders).pack(side=tk.LEFT, padx=5)
        self.orders_tree = ttk.Treeview(tab, columns=("id", "time", "table", "amount"), show="headings")
        self.orders_tree.heading("id", text="订单ID")
        self.orders_tree.heading("time", text="下单时间")
        self.orders_tree.heading("table", text="桌号")
        self.orders_tree.heading("amount", text="总金额")
        self.orders_tree.column("id", width=80, anchor=tk.CENTER)
        self.orders_tree.column("time", width=180, anchor=tk.CENTER)
        self.orders_tree.column("table", width=80, anchor=tk.CENTER)
        self.orders_tree.column("amount", width=100, anchor=tk.E)
        self.orders_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.load_orders()

    def load_orders(self):
        self.orders_tree.delete(*self.orders_tree.get_children())
        query = """
        SELECT 
            o.order_id, 
            MIN(o.order_time) AS order_time,
            o.table_id, 
            SUM(o.subtotal) AS total_amount
        FROM orders o
        GROUP BY o.order_id, o.table_id
        ORDER BY order_time DESC
        """
        data = self.db.query(query)
        for row in data:
            self.orders_tree.insert("", tk.END, values=(
                row["order_id"],
                row["order_time"].strftime("%Y-%m-%d %H:%M:%S"),
                row["table_id"],
                f"{row['total_amount']:.2f}元"
            ))
if __name__ == "__main__":
    root = tk.Tk()
    app = AdminApp(root)
    root.mainloop()
