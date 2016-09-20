"""
Preprocessing Transformers
"""
# import numpy as np
import pandas as pd
from sklearn.base import TransformerMixin


class CategoricalEncoder(TransformerMixin):
    def __init__(self, categories: dict=None, ordered: dict=None):
        self.categories = categories or {}
        self.ordered = ordered or {}
        self.cat_cols_ = None

    def fit(self, X, y=None):
        if not len(self.categories):
            categories = X.select_dtypes(include=[object]).columns
        else:
            categories = self.categories
        self.cat_cols_ = categories
        return self

    def transform(self, X: pd.DataFrame, y=None) -> pd.DataFrame:
        X = X.copy()
        categories = self.cat_cols_
        for k in categories:
            cat = (categories.get(k, None)
                   if hasattr(categories, 'get')
                   else None)
            ordered = self.ordered.get(k, False)
            X[k] = pd.Categorical(X[k],
                                  categories=cat,
                                  ordered=ordered)
        return X


class DummyEncoder(TransformerMixin):

    def __init__(self, columns: list=None, drop_first=True):
        self.columns = columns
        self.drop_first = drop_first

        self.index_ = None
        self.columns_ = None
        self.cat_columns_ = None  # type: pd.Index
        self.non_cat_columns_ = None  # type: pd.Index
        self.cat_map_ = None
        self.cat_blocks_ = None

    def fit(self, X, y=None):
        self.index_ = X.index
        self.columns_ = X.columns
        if self.columns is None:
            self.cat_columns_ = X.select_dtypes(include=['category']).columns
        else:
            self.cat_columns_ = self.columns
        self.non_cat_columns_ = X.columns.drop(self.cat_columns_)

        self.cat_map_ = {col: X[col].cat for col in self.cat_columns_}

        left = len(self.non_cat_columns_)
        self.cat_blocks_ = {}
        for col in self.cat_columns_:
            right = left + len(X[col].cat.categories)
            self.cat_blocks_[col], left = slice(left, right), right
        return self

    def transform(self, X, y=None):
        return pd.get_dummies(X, drop_first=self.drop_first)

    def inverse_transform(self, X):
        raise NotImplementedError
        non_cat = pd.DataFrame(X[:, :len(self.non_cat_columns_)],
                               columns=self.non_cat_columns_)
        cats = []
        for col, cat in self.cat_map_.items():
            slice_ = self.cat_blocks_[col]
            codes = X[:, slice_].argmax(1)
            series = pd.Series(pd.Categorical.from_codes(
                codes, cat.categories, ordered=cat.ordered
            ), name=col)
            cats.append(series)
        df = pd.concat([non_cat] + cats, axis=1)[self.columns_]
        return df
