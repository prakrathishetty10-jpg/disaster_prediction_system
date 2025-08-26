from tkinter import *
from tkinter import ttk, messagebox
import sqlite3

class AdminDashboard:
    def __init__(self, master):
        self.master = master
        self.master.title("Admin Dashboard")
        self.master.geometry("800x600")
        self.master.configure(bg='white')

        # Connect to the database
        self.conn = sqlite3.connect('earthquake_predictions.db')
        self.cursor = self.conn.cursor()

        # Create the GUI components
        self.create_widgets()

    def create_widgets(self):
        # Show all prediction history
        Label(self.master, text='All Prediction History:', font=('Arial', 12, 'bold'), bg='white').pack(pady=10)
        self.history_tree = ttk.Treeview(self.master, columns=('id', 'latitude', 'longitude', 'magnitude', 'location', 'status', 'user_id', 'created_at'), show='headings')
        self.history_tree.heading('id', text='Id')
        self.history_tree.heading('latitude', text='Latitude')
        self.history_tree.heading('longitude', text='Longitude')
        self.history_tree.heading('magnitude', text='Magnitude')
        self.history_tree.heading('location', text='Location')
        self.history_tree.heading('status', text='Status')
        self.history_tree.heading('user_id', text='User_id')
        self.history_tree.heading('created_at', text='Created_at')

        # Set wider column for location
        self.history_tree.column('location', width=350)
        self.history_tree.column('id', width=50)
        self.history_tree.column('latitude', width=80)
        self.history_tree.column('longitude', width=80)
        self.history_tree.column('magnitude', width=80)
        self.history_tree.column('status', width=120)
        self.history_tree.column('user_id', width=80)
        self.history_tree.column('created_at', width=140)

        self.history_tree.pack(pady=5, fill='both', expand=True)

        # Delete button
        delete_btn = Button(self.master, text="Delete Selected History", command=self.delete_selected_history, bg='red', fg='white', font=('Arial', 10, 'bold'))
        delete_btn.pack(pady=10)

        # Right-click menu
        self.menu = Menu(self.master, tearoff=0)
        self.menu.add_command(label="Delete", command=self.delete_selected_history)
        self.history_tree.bind("<Button-3>", self.show_context_menu)

    def load_prediction_history(self):
        # Clear the treeview
        for i in self.history_tree.get_children():
            self.history_tree.delete(i)

        # Get the prediction history from the database
        self.cursor.execute("SELECT * FROM predictions")
        rows = self.cursor.fetchall()

        # Insert the data into the treeview
        for row in rows:
            self.history_tree.insert('', 'end', values=row)

    def delete_selected_history(self):
        selected = self.history_tree.selection()
        if not selected:
            messagebox.showwarning("Delete History", "No history selected.")
            return
        history_id = self.history_tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Delete History", f"Are you sure you want to delete history ID {history_id}?"):
            self.cursor.execute("DELETE FROM predictions WHERE id=?", (history_id,))
            self.conn.commit()
            self.history_tree.delete(selected[0])

    def show_context_menu(self, event):
        selected = self.history_tree.identify_row(event.y)
        if selected:
            self.history_tree.selection_set(selected)
            self.menu.post(event.x_root, event.y_root)

    def __del__(self):
        # Close the database connection when the object is deleted
        self.conn.close()

def main():
    root = Tk()
    app = AdminDashboard(root)
    root.mainloop()

if __name__ == "__main__":
    main()