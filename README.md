# Twitter Bot for Real Estate Recommendations

## Overview

This project involves the development of a Twitter bot that autonomously selects and promotes high-value real estate properties based on their cost-to-value ratio. The bot connects to a real estate database, analyzes the data to identify the best deals, and generates engaging tweets that are posted on Twitter. The main goal is to attract a broad audience interested in real estate investments in Istanbul, Turkey by promoting properties with the most appealing value propositions.

### Objectives

- **Data Analysis and Selection**: Identify properties with the best value/cost ratio by analyzing real estate data.
    
- **Information Summarization**: Extract and condense essential information from property listings into a brief, Twitter-friendly format.
    
- **Twitter Bot Development**: Automate tweets with the extracted property data to engage with potential buyers.
    
- **Audience Engagement**: Maximize engagement and follower growth on Twitter through targeted and well-crafted tweets.
    

## Features

- **Database Integration**: Connects to a real estate database to fetch property data.
    
- **Data Analysis**: Uses statistical and machine learning models to evaluate property values and select top properties.
    
- **Natural Language Processing (NLP)**: Summarizes property descriptions into short, appealing tweets.
    
- **Twitter API**: Posts property recommendations to Twitter automatically.
    
- **Analytics and Monitoring**: Tracks the performance of the bot, including follower growth and engagement metrics.
    

## Getting Started

### Prerequisites

- **Python 3.8+**
    
- **Pandas**, **NumPy**, **scikit-learn**, **transformers**, **nltk**, **matplotlib**
    
- **Twitter API Access**: Requires Twitter Developer account to get API keys for automating tweets.
    
- **Real Estate Dataset**: The project requires a real estate dataset with property details, including features like location, price, room count, and more.
    

### Installation

1. Clone this repository:
    
    ```
    git clone https://github.com/mhsendur/RealEstateTweetBot
    ```
    
2. Install required dependencies.
    
3. Set up Twitter API credentials.
    

## Model Training and Evaluation

- **Model Type**: Random Forest, Gradient Boosting, and XGBoost have been tested for value prediction.
    
- **Feature Engineering**: A significant effort has been made in feature engineering to improve the model's predictive performance. Below is a detailed overview of the feature engineering process and features that have been tried:
    
    - **District-Level Features**: Several district-based features have been integrated, such as:
        
        - **Population Density**: The number of people per square kilometer in each district.
            
        - **Population Count**: Total population of each district.
            
        - **Population Growth Rate**: Yearly growth rate of the population in each district.
            
        - **Socio-Demographic and Socio-Economic Scores**: These scores represent socio-demographic and socio-economic conditions in each district, which provide insights into the living standards and quality of the area.
            
        - **Healthcare Accessibility**: Distance to various healthcare facilities such as pharmacies, family health centers, and hospitals.
            
        - **Social Assistance Information**: Number of households in each district receiving or not receiving social assistance.
            
        - **Average Household Size (m²)**: Average gross and net household sizes in each district.
            
    - **Property-Level Features**: Features directly related to property listings, including:
        
        - **Room Count, Bath Count, and Floor Information**: Basic property features such as the number of rooms, bathrooms, and floor details.
            
        - **Net and Gross Area**: The net and gross sizes of the property in square meters.
            
        - **Location Features**: Latitude, longitude, distance to the sea, distance to malls, and other amenities.
            
        - **Amenity Scores**: Presence of amenities like pools, balconies, and security, represented as binary features.
            
        - **Sentiment Analysis of Descriptions**: Sentiment analysis of property descriptions to understand if positive or compelling language impacts property value.
            
        - **Keyword Analysis**: Specific keywords in descriptions (e.g., "urgent", "close to metro") were used as binary features to capture the effect of specific selling points.
            
    - **Interaction Features**: Combinations of features that could capture non-linear relationships, such as:
        
        - **Room-to-Bathroom Ratio**: To capture the balance between rooms and bathrooms.
            
        - **Age-to-Floor Ratio**: To see how building age relates to the number of floors.
            
    - **Geospatial Clustering**: Properties were clustered based on geographic coordinates to create a categorical "location cluster" feature that captures regional trends better than latitude and longitude alone.
        
- **Performance Metrics**: Models are evaluated based on Mean Squared Error (MSE), Root Mean Squared Error (RMSE), Mean Absolute Error (MAE), and R² score.

## Contributors

- Mustafa Harun Sendur
- Melih Cihan Kiziltoprak
- Ceren Sahin
- Dila Karatas

---

This project has been built for educational purposes only.
