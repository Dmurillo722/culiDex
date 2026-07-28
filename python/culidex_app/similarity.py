import numpy as np
import pandas as pd
from scipy.stats import zscore
import numpy.typing as npt
from collections import OrderedDict

from . import db
from . import _culidex as culidex

WEIGHTS = np.array([
    #0.00,  # category        — categorical, excluded
    1.00,  # energy_kcal     — redundant with macro sum
    1.50,  # water_g         — concentration/intensity multiplier
    3.50,  # protein_g       — umami potential, Maillard character
    4.00,  # fat_total_g     — richness, mouthfeel
    1.50,  # carb_g          — starchy character
    1.50,  # fiber_g         — texture, astringency
    4.00,  # sugars_total_g  — sweetness (aggregate)
    2.50,  # fat_saturated_g — dairy/meat richness
    1.50,  # fat_monounsat_g — neutral fat, weakest signal
    1.50,  # fat_polyunsat_g — fish/nut character
    1.50,  # cholesterol_mg  — animal product proxy
    1.50,  # glucose_g       — fruit-forward sweetness
    2.50,  # fructose_g      — fruit-forward sweetness
    1.50,  # sucrose_g       — neutral sweet
    2.00,  # lactose_g       — dairy sweet
    5.00,  # sodium_mg       — saltiness, primary taste dimension
    2.00,  # potassium_mg    — subtle bitter/salty at high concentrations
    1.50,  # calcium_mg      — chalky, dairy association
    1.50,  # magnesium_mg    — mild bitterness
    2.50,  # iron_mg         — metallic notes (red meat, blood, liver)
    2.00,  # zinc_mg         — metallic/savory
    0.50,  # phosphorus_mg   — structural, weak flavor signal
    3.00,  # vitamin_c_mg    — sourness/acidity proxy
    2.50,  # niacin_mg       — umami precursor
    0.01,  # thiamin_mg      — negligible direct flavor
    0.01,  # riboflavin_mg   — negligible direct flavor
    0.01,  # vitamin_b6_mg   — negligible direct flavor
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
    numerical_df = numerical_df.fillna(numerical_df.mean())
    numerical_matrix = numerical_df[:].values
    numerical_matrix = numerical_matrix*weights
    row_norms = np.linalg.norm(numerical_matrix, axis = 1, keepdims=True)
    numerical_matrix = numerical_matrix/row_norms

    return numerical_matrix


def _build_matrix(df : pd.DataFrame, weights : np.array):
    """
    Function used to build a normalized matrix from the data for faster computation time

    Retruns a matrix of  weighted data points for cosine similarity computation
    The non numerical columns are dropped and all NaN values are filled with 0s
    This function is for the purpose of trying updated logic for the rust cosine
    similarity in which the zero value entries are dropped entirely for comparison
    Params :

    df : a pandas dataframe
    """
    numerical_df = df.drop(columns = ['name', 'category', 'country'])
    numerical_df = numerical_df.fillna(numerical_df.mean())
    numerical_df = numerical_df.apply(zscore, nan_policy='omit')
    numerical_matrix = numerical_df[:].values
    numerical_matrix = numerical_matrix*weights

    return numerical_matrix



#this function will be useful later on when implementing only within same category search
def _build_category_mapping(df):
    """
    Builds a mapping in the form of:

    Category name - > (all corresponding indices of foods that fall in that category)
    """

    return {cat : np.where(df['category'] == cat)[0] for cat in df['category'].unique()}


def _build_index_list(cat_dict : dict[str,npt.NDArray[np.int32]], categories : set[str]):
    """
    This function is used to build a concatenated list of useful indices for comparison
    to pass to the rust similarity calculator
    """
    arrays = [cat_dict[cat] for cat in categories]
    if not arrays:
        return np.array([], dtype=np.int64)

    return np.concatenate(arrays)


def _build_food_names(df):
    return df["name"].to_numpy()

def get_substitutes(foodName, food_names, indices, matrix, top_n):

    query_ind = np.where(foodName == food_names)[0][0]
    query = matrix[query_ind]
    #request one extra to drop the food matching itself (always score 1.0)
    results = culidex.cosine_scores(indices.tolist(), matrix.tolist(), query.tolist(), top_n + 1)
    results = [(i, score) for i, score in results if i != query_ind]

    return results[:top_n]

class cacheEntry:

    def __init__(self):
        self.categories = set()
        self.entries = []

    def get_categories(self):
        return self.categories

    def get_entries(self):
        # return a copy so callers can't mutate the cached list in place
        return list(self.entries)

    def set_categories(self, new_cats):
        self.categories = set(new_cats)

    def set_entries(self, new_ents):
        for i, score in new_ents:
            self.entries.append((i, score))


class recentCache:
    def __init__(self, maxSize):
        self.cache : OrderedDict[str , cacheEntry] = OrderedDict()
        self.maxSize=maxSize

    def get(self, foodName, categories):
        #cache miss on foodname or categories have changed since last time
        if foodName not in self.cache or self.cache[foodName].get_categories() != categories:
            return None

        #key was most recently used
        self.cache.move_to_end(foodName)
        return self.cache[foodName]

    def put(self, foodName, result, categories):
        #if already in the cache and the categories are the same, move it to the end of the cache (most recently used)
        if foodName in self.cache:
            if self.cache[foodName].get_categories() == categories:
                self.cache.move_to_end(foodName)
                return #return ro prevent duplicate addition
            else:
                #categories have changed, remove the old entry
                self.cache.pop(foodName)

        elif len(self.cache) >= self.maxSize:
            #remove the first item (leas)
            self.cache.popitem(last=False)

        #create the new cache entry and add it to the cache
        entry = cacheEntry()
        entry.set_categories(categories)
        entry.set_entries(result)
        self.cache[foodName] = entry


#_df = db.fetch_all()
#_matrix = _build_normalized_matrix(_df, WEIGHTS)
#cat_map = _build_category_mapping(_df)
