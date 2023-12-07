import streamlit as st
import pandas as pd
import numpy as np
import pickle
from bs4 import BeautifulSoup
import requests
import runGA

def ga_algo(csv_file,height,weight,gender,age,phy_activity,bmi_level):
    recipe_file=pd.read_csv(csv_file)
    chromosome_length=float(recipe_file.shape[0])
    ohe_meals=pd.get_dummies(recipe_file['Meal'])
    calories_csv=recipe_file['Calories']
    protein_csv=recipe_file['Protein']
    carbs_csv=recipe_file['Carbs']
    fat_csv=recipe_file['Fat']
    A=np.vstack((calories_csv,protein_csv,carbs_csv,fat_csv,ohe_meals['Breakfast'],ohe_meals['Entrée'],ohe_meals['Protein'],
                 ohe_meals['Side'],ohe_meals['Soup']))
    A=A.astype(float)
    cal,pro,carbs,fat=calculate_macros(height,weight,gender,age,phy_activity,bmi_level)
    b=[cal,pro,carbs,fat,2,2,2,2,2]
    b=np.array(b)
    b=b.astype(float)
    #ga
    gaAnalyzer = runGA.initialize()
    y=gaAnalyzer.runGA(chromosome_length,A,b)
    y=np.array(y)
    binary_array = (y >= 0.5).astype(int).T
    filtered_data=recipe_file[binary_array==1]
    drop_cols=['Servings','Cuisine','ProteinSource','Notes']
    dropped_df=filtered_data.drop(columns=drop_cols)
    drop_index=dropped_df.reset_index(drop=True)
    drop_index=drop_index.rename(columns={'URL':'Recipe Links'})
    calories=drop_index['Calories'].sum()
    protein=drop_index['Protein'].sum()
    fats=drop_index['Fat'].sum()
    carbz=drop_index['Carbs'].sum()
    return drop_index,calories,protein,carbz,fats


def calculate_macros(height, weight, gender, age, phy_activity,bmi_level):
    url = "https://www.calculator.net/macro-calculator.html"

    if gender=="Male":
        gender_par="m"
    else:
        gender_par="f"
    
    if phy_activity== 0:
        td= 1.2
    elif phy_activity==1:
        td= 1.375
    elif phy_activity==2:
        td= 1.465
    elif phy_activity==3:
        td==1.55
    elif phy_activity==4:
        td= 1.725
    else:
        td== 1

    if bmi_level=='Insufficient_Weight':
        cg='g1'
    elif bmi_level=='Overweight_Level_I' or bmi_level=='Overweight_Level_II':
        cg='l'
    elif bmi_level=='Obesity_Level_I':
        cg='l1'
    elif bmi_level=='Obesity_Level_II' or bmi_level=='Obesity_Level_III':
        cg='l2'
    else:
        cg='m'

    params = {
        "ctype": "metric",
        "cage": age,
        "csex": gender_par,
        "cheightmeter": height,
        "ckg": weight,
        "cactivity": td,
        "cgoal":cg,
        "printit": 0,
        "x": 121,
        "y": 28
    }

    response = requests.get(url, params=params)

    soup = BeautifulSoup(response.content, 'html.parser')

    macros = dict()

    labels = soup.find_all('td', {'class': 'arrow_box'})
    values = soup.find_all('td', {'class': 'result_box'})
    for label, value in zip(labels, values):
        temp_lab = label.div.text.strip()
        temp_val = value.text.replace('<', '').replace(':', '').strip().split(" ")
        macros[temp_lab+" ("+temp_val[1]+")"] = temp_val[0]

    carbs=int(macros['Carbs (grams/day)'])
    protein=int(macros['Protein (grams/day)'])
    fat=int(macros['Fat (grams/day)'])
    cal=macros['Food Energy (Calories/dayor)'].replace(',', '')
    cal=int(cal)
    return cal,protein,carbs,fat
 
    
 
def app():
    # Title of the app
    st.title("Food Recommender System")

    # User input section
    st.sidebar.header("User Information")

    # Get user's age using a text input box
    age = st.sidebar.text_input("Enter Your Age", "25")

    # Convert the age input to an integer
    age = int(age) if age.isdigit() else 25

    # Get user's gender
    gender = st.sidebar.selectbox("Select Your Gender", ["Male", "Female"])

    # Get user's weight
    weight = st.sidebar.number_input("Enter Your Weight (kg)", min_value=1, max_value=500, value=70)

    # Get user's height
    height = st.sidebar.number_input("Enter Your Height (cm)", min_value=1, max_value=300, value=170)

     # Dropdown menu for activity level
    activity_options = {
     "Sedentary: little or no exercise": 0,
     "Light: exercise 1-3 times/week": 1,
     "Moderate: exercise 4-5 times/week": 2,
     "Active: daily exercise or intense exercise 3-4 times/week": 3,
     "Very Active: intense exercise 6-7 times/week": 4,
     "Extra Active: very intense exercise daily, or physical job": 5
     }

    activity_level = st.sidebar.selectbox("Select Your Activity Level", list(activity_options.keys()))

    # Collects user input features into dataframe, set other features to default values
    data = {
            'Gender': gender,
            'Age': age,
            'Height': height/100,
            'Weight': weight,
            'family_history_with_overweight': 1.0,
            'FAVC': 1.0,
            'FCVC': 2.0,
            'NCP': 2.5, 
            'CAEC': 2.0,
            'SMOKE': 0.0,
            'CH2O': 2.0,
            'SCC': 0.0,
            'FAF': activity_options,
            'TUE': 1.0,
            'CALC': 2.0,
            'MTRANS': 3.0
    }
    input_df = pd.DataFrame(data)


    # Encoding of ordinal features
    input_df['Gender'] = input_df['Gender'].replace({
    'Female': 0.0,
    'Male': 1.0
    })

    input_df['FAF'] = input_df['FAF'].replace({
        'Sedentary: little or no exercise': 0.0,
        'Light: exercise 1-3 times/week': 0.6,
        "Moderate: exercise 4-5 times/week": 1.2, 
        "Active: daily exercise or intense exercise 3-4 times/week": 1.8, 
        "Very Active: intense exercise 6-7 times/week": 2.4, 
        "Extra Active: very intense exercise daily, or physical job": 3.0
    })

    # Display BMI
    BMI = weight/(height**2)*10000
    BMI = round(BMI, 1)
    st.write(f"Your BMI is {BMI} kg/m\u00B2.")

    # Button to trigger recommendations
    if st.sidebar.button("Get Food Recommendations"):
        # Display loading spinner while the recommender system is processing
        with st.spinner("Calculating Weight Level..."):
            # Simulate a delay to mimic the time taken by the recommender system


            # Reads in saved classification model
            load_clf = pickle.load(open('apps\Models\obesity_clf.pkl', 'rb'))
            


            # Placeholder for obesity level (replace with actual logic)
            # Apply model to make predictions
            obesity_num = load_clf.predict(input_df)[0]
            levels_in_order = ['Insufficient_Weight', 'Normal_Weight', 'Obesity_Type_I','Obesity_Type_II','Obesity_Type_III','Overweight_Level_I','Overweight_Level_II']
            obesity_level=levels_in_order[obesity_num]
            
            # Display obesity level
            st.subheader("Your Obesity Level")
            st.write(f"Based on the information provided, your weight classification is: {obesity_level}")
            

            
        with st.spinner("Calculating Suggested Macros..."):

            # Call your friend's function to calculate macros
            cal, protein, carbs, fat = calculate_macros(
            height, weight, gender, age, activity_options[activity_level], obesity_level
            )
            # Hide the first spinner and display a message
        st.success("Calculation of Macros Complete!")
        # Display suggested macros from calculate_macros
        st.subheader("Suggested Macros:")
        st.write(f"Calories(cal): {cal}")
        st.write(f"Protein(grams): {protein}")
        st.write(f"Carbs(grams): {carbs}")
        st.write(f"Fats(grams): {fat}")
        
    # Display the second spinner while ga_algo is processing
        with st.spinner("Generating Meals Recommendations..."):
            # Call your friend's function
            recipe_file = "Recipes@.csv"
            drop_index, calories, protein, carbz, fats = ga_algo(
                recipe_file, height, weight, gender, age, activity_options[activity_level], obesity_level
            )

        # Display DataFrame from friend's function
        st.subheader("Meals Recommended:")
        st.dataframe(drop_index)
        
        # Use markdown for a smaller text style
        st.markdown("**Total Nutritional Information for the Recommended Foods:**")
        
        st.markdown("#### Calories:")
        st.write(f"Calories(cal): {calories}")
        
        st.markdown("#### Protein:")
        st.write(f"Protein(grams): {protein}")
        
        st.markdown("#### Carbs:")
        st.write(f"Carbs(grams): {carbz}")
        
        st.markdown("#### Fats:")
        st.write(f"Fats(grams): {fats}")

       
    # Display some information or instructions
    st.info("Enter your details on the left sidebar and click 'Get Food Recommendations' to see personalized suggestions-BY YOURS TRUELY BEN NGUYEN")