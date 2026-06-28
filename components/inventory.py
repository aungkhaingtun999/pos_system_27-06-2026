import streamlit as st
import pandas as pd
# အရေးကြီး: အပြင်ဖိုင်များကို မခေါ်ဘဲ components ထဲမှသာ import လုပ်ပါ
from components.supabase_logic import supabase

# ==========================================
# 1. Helper Functions (Logic)
# ==========================================
def get_products_fresh():
    """Database မှ ပစ္စည်းစာရင်းကို အသစ်ပြန်ဆွဲယူခြင်း (Cache ပြဿနာမရှိစေရန်)"""
    if not supabase: return []
    try:
        response = supabase.table("products").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching products: {e}")
        return []

def _update_inventory_db(edited_df):
    """ဇယားမှ ပြောင်းလဲမှုများကို Supabase သို့ ပေးပို့ခြင်း"""
    try:
        for _, row in edited_df.iterrows():
            supabase.table("products").update({
                "stock_qty": int(row["stock_qty"]),
                "sell_price": float(row["sell_price"])
            }).eq("barcode", row["barcode"]).execute()
        return True
    except Exception as e:
        st.error(f"Error updating inventory: {e}")
        return False

# ==========================================
# 2. Inventory UI
# ==========================================
def show_inventory():
    """Inventory Management UI ကို render လုပ်ပေးသော Main module"""
    st.title("📦 Inventory Management")
    
    products = get_products_fresh()
    if not products:
        st.warning("ပစ္စည်းစာရင်း မရှိသေးပါ။")
        return

    df = pd.DataFrame(products)
    
    # Inventory Editor
    edited_df = st.data_editor(
        df, 
        column_config={
            "stock_qty": st.column_config.NumberColumn("Stock Qty", min_value=0),
            "sell_price": st.column_config.NumberColumn("Sell Price", format="%,.0f MMK"),
        },
        use_container_width=True
    )
    
    # Save Changes
    if st.button("💾 ပြောင်းလဲမှုများ သိမ်းဆည်းမည်"):
        with st.spinner("Saving changes..."):
            if _update_inventory_db(edited_df):
                st.success("Inventory အောင်မြင်စွာ Update လုပ်ပြီးပါပြီ။")
                st.rerun()

    # Low Stock Alert
    low_stock = df[df["stock_qty"] <= 5]
    if not low_stock.empty:
        st.error("⚠️ အောက်ပါပစ္စည်းများမှာ Stock နည်းနေပါပြီ:")
        st.dataframe(low_stock[["product_name", "stock_qty"]], use_container_width=True)
