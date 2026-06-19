import numpy as np
import db
import pandas as pd
import culidex

WEIGHTS = np.array([
    #0.00,  # category        — categorical, excluded
    0.25,  # energy_kcal     — redundant with macro sum
    1.00,  # water_g         — concentration/intensity multiplier
    3.00,  # protein_g       — umami potential, Maillard character
    3.00,  # fat_total_g     — richness, mouthfeel
    1.50,  # carb_g          — starchy character
    1.50,  # fiber_g         — texture, astringency
    3.00,  # sugars_total_g  — sweetness (aggregate)
    2.00,  # fat_saturated_g — dairy/meat richness
    1.00,  # fat_monounsat_g — neutral fat, weakest signal
    2.00,  # fat_polyunsat_g — fish/nut character
    1.00,  # cholesterol_mg  — animal product proxy
    2.00,  # glucose_g       — fruit-forward sweetness
    2.00,  # fructose_g      — fruit-forward sweetness
    2.00,  # sucrose_g       — neutral sweet
    2.00,  # lactose_g       — dairy sweet
    3.00,  # sodium_mg       — saltiness, primary taste dimension
    1.00,  # potassium_mg    — subtle bitter/salty at high concentrations
    1.00,  # calcium_mg      — chalky, dairy association
    1.00,  # magnesium_mg    — mild bitterness
    1.50,  # iron_mg         — metallic notes (red meat, blood, liver)
    1.50,  # zinc_mg         — metallic/savory
    0.50,  # phosphorus_mg   — structural, weak flavor signal
    3.00,  # vitamin_c_mg    — sourness/acidity proxy
    1.00,  # niacin_mg       — umami precursor
    0.50,  # thiamin_mg      — negligible direct flavor
    0.50,  # riboflavin_mg   — negligible direct flavor
    0.50,  # vitamin_b6_mg   — negligible direct flavor
])

def _build_normalized_matrix(df : pd.DataFrame, weights : np.array):
    """
    Function used to build a normalized matrix from the data for faster computation time

    Retruns a matrix of normalized and weighted data points for cosine similarity computation
    The non numerical columns are dropped and all NaN values are filled with 0s
    Params :

    df : a pandas dataframe
    """
    numerical_df = df.drop(columns = ['name', 'category', 'country'])
    numerical_df = numerical_df.fillna(0)
    numerical_matrix = numerical_df[:].values
    numerical_matrix = numerical_matrix*weights
    row_norms = np.linalg.norm(numerical_matrix, axis = 1, keepdims=True)
    numerical_matrix = numerical_matrix/row_norms

    return numerical_matrix


#this function will be useful later on when implementing only within same category search
def _build_category_mapping(df):
    """
    Builds a mapping in the form of:
    
    Category name - > (all corresponding indices of foods that fall in that category)
    """

    return {cat : np.where(df['category'] == cat)[0] for cat in df['category'].unique()}

def _build_food_names(df):
    return df["name"].to_numpy()

def get_substitutes(foodName, food_names, matrix, top_n):

    query_ind = np.where(foodName == food_names)[0][0]
    query = matrix[query_ind]

    #request one extra to drop the food matching itself (always score 1.0)
    results = culidex.cosine_scores(matrix.tolist(), query.tolist(), top_n + 1)
    results = [(i, score) for i, score in results if i != query_ind]

    return results[:top_n]


#_df = db.fetch_all()
#_matrix = _build_normalized_matrix(_df, WEIGHTS)
#cat_map = _build_category_mapping(_df)