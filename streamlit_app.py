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
st.write("The name on your smoothie will be:", name_on_order)

# Connect to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Get both FRUIT_NAME and SEARCH_ON
sp_df = session.table("smoothies.public.fruit_options").select(
    col("FRUIT_NAME"), col("SEARCH_ON")
)

# Convert Snowpark DF -> Pandas DF
pd_df = sp_df.to_pandas()

# Multiselect shows fruit names
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients",
    options=pd_df["FRUIT_NAME"].tolist(),
    max_selections=5
)

if ingredients_list:
    ingredients_string = ""

    for each_fruit in ingredients_list:
        ingredients_string += each_fruit + " "

        # Find the SEARCH_ON value for API
        search_on = pd_df.loc[pd_df["FRUIT_NAME"] == each_fruit, "SEARCH_ON"].iloc[0]

        st.subheader(each_fruit + " Nutrition Information")

        # Call API
        fruityvice_response = requests.get("https://fruityvice.com/api/fruit/" + search_on)

        if fruityvice_response.ok:
            data = fruityvice_response.json()

            # Flatten nutrition info into rows
            nutrition = data["nutritions"]
            df = pd.DataFrame({
                "nutrition": list(nutrition.keys()),
                "value": list(nutrition.values())
            })

            # Add other metadata columns (family, genus, id, name, order)
            df["family"] = data.get("family", "")
            df["genus"] = data.get("genus", "")
            df["id"] = data.get("id", "")
            df["name"] = data.get("name", "")
            df["order"] = data.get("order", "")

            # Reorder columns
            df = df[["nutrition", "family", "genus", "id", "name", "value", "order"]]

            # Show dataframe
            st.dataframe(df, use_container_width=True)
        else:
            st.warning(f"No data found for {each_fruit} (searched as '{search_on}')")

    # Insert order into Snowflake
    my_insert_stmt = f"""
        insert into smoothies.public.orders(ingredients, name_on_order)
        values ('{ingredients_string}', '{name_on_order}')
    """

    if st.button("Submit Order"):
        session.sql(my_insert_stmt).collect()
        st.success("Your Smoothie is ordered, " + name_on_order + "!", icon="✅")
