# streamlit_app.py

# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import requests
import pandas as pd

# Title
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie")

# Input: name on order
name_on_order = st.text_input("Name on smoothie", "Pooja")
st.write("The name on your smoothie will be", name_on_order)

# Connect to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# 1) Get BOTH columns needed from Snowflake
sp_df = (
    session.table("smoothies.public.fruit_options")
    .select(col("FRUIT_NAME"), col("SEARCH_ON"))
)

# 2) Convert Snowpark DF -> Pandas DF
pd_df = sp_df.to_pandas()

# 3) Multiselect should show the friendly FRUIT_NAMEs
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients",
    options=pd_df["FRUIT_NAME"].tolist(),
    max_selections=5
)

if ingredients_list:
    st.write("You selected:", ingredients_list)

    # Build a string of chosen fruits (display names) for the order table
    ingredients_string = " ".join(ingredients_list)

    API_BASE = "https://fruityvice.com/api/fruit"

    # 4) For each chosen fruit, map to SEARCH_ON and call the API
    for fruit_chosen in ingredients_list:
        # Lookup the API search term
        search_on = pd_df.loc[
            pd_df["FRUIT_NAME"] == fruit_chosen, "SEARCH_ON"
        ].iloc[0]

        st.subheader(f"{fruit_chosen} Nutrition Information")

        # Call API
        fruityvice_response = requests.get(f"{API_BASE}/{search_on}")
        if fruityvice_response.ok:
            fv_df = pd.DataFrame([fruityvice_response.json()])
            st.dataframe(fv_df, use_container_width=True)
        else:
            st.warning(f"No data found for {fruit_chosen} (searched as '{search_on}')")

    # 5) Insert the order into Snowflake
    my_insert_stmt = f"""
        insert into smoothies.public.orders(ingredients, name_on_order)
        values ('{ingredients_string}', '{name_on_order}')
    """

    if st.button("Submit Order"):
        session.sql(my_insert_stmt).collect()
        st.success(f"Your Smoothie is ordered, {name_on_order}!", icon="✅")
