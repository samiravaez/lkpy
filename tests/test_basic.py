from lenskit.algorithms import basic

import pandas as pd
import numpy as np

import lk_test_utils as lktu
from pytest import approx, mark

simple_df = pd.DataFrame({'item': [1, 1, 2, 3],
                          'user': [10, 12, 10, 13],
                          'rating': [4.0, 3.0, 5.0, 2.0]})


def test_precomputed():
    algo = basic.Memorized(simple_df)

    preds = algo.predict(None, 10, [1, 2])
    assert set(preds.index) == set([1, 2])
    assert all(preds == pd.Series({1: 4.0, 2: 5.0}))

    preds = algo.predict(None, 12, [1, 3])
    assert set(preds.index) == set([1, 3])
    assert preds.loc[1] == 3.0
    assert np.isnan(preds.loc[3])


def test_fallback_train_one():
    algo = basic.Fallback(basic.Bias())
    model = algo.train(lktu.ml_pandas.renamed.ratings)
    assert len(model) == 1
    assert isinstance(model[0], basic.BiasModel)
    assert model[0].mean == approx(lktu.ml_pandas.ratings.rating.mean())


def test_fallback_train_one_pred_impossible():
    algo = basic.Fallback(basic.Memorized(simple_df))
    model = algo.train(lktu.ml_pandas.renamed.ratings)
    assert len(model) == 1

    preds = algo.predict(model, 10, [1, 2])
    assert set(preds.index) == set([1, 2])
    assert all(preds == pd.Series({1: 4.0, 2: 5.0}))

    preds = algo.predict(model, 12, [1, 3])
    assert set(preds.index) == set([1, 3])
    assert preds.loc[1] == 3.0
    assert np.isnan(preds.loc[3])


def test_fallback_predict():
    algo = basic.Fallback(basic.Memorized(simple_df), basic.Bias())
    model = algo.train(lktu.ml_pandas.renamed.ratings)
    assert len(model) == 2
    assert isinstance(model[1], basic.BiasModel)
    assert model[1].mean == approx(lktu.ml_pandas.ratings.rating.mean())

    # first user + item
    preds = algo.predict(model, 10, [1])
    assert preds.loc[1] == 4.0
    # second user + first item
    preds = algo.predict(model, 15, [1])
    assert preds.loc[1] == approx(model[1].mean + model[1].users.loc[15] + model[1].items.loc[1])

    # second item + user item
    preds = algo.predict(model, 12, [2])
    assert preds.loc[2] == approx(model[1].mean + model[1].users.loc[12] + model[1].items.loc[2])

    # blended
    preds = algo.predict(model, 10, [1, 5])
    assert preds.loc[1] == 4.0
    assert preds.loc[5] == approx(model[1].mean + model[1].users.loc[10] + model[1].items.loc[5])

    # blended unknown
    preds = algo.predict(model, 10, [5, 1, -23081])
    assert len(preds) == 3
    assert preds.loc[1] == 4.0
    assert preds.loc[5] == approx(model[1].mean + model[1].users.loc[10] + model[1].items.loc[5])
    assert preds.loc[-23081] == approx(model[1].mean + model[1].users.loc[10])


def test_fallback_save_load(tmp_path):
    tmp_path = lktu.norm_path(tmp_path)

    algo = basic.Fallback(basic.Memorized(simple_df), basic.Bias())
    original = algo.train(lktu.ml_pandas.renamed.ratings)

    fn = tmp_path / 'fallback'
    algo.save_model(original, fn)

    model = algo.load_model(fn)

    assert len(model) == 2
    assert isinstance(model[1], basic.BiasModel)
    assert model[1].mean == approx(lktu.ml_pandas.ratings.rating.mean())

    # first user + item
    preds = algo.predict(model, 10, [1])
    assert preds.loc[1] == 4.0
    # second user + first item
    preds = algo.predict(model, 15, [1])
    assert preds.loc[1] == approx(model[1].mean + model[1].users.loc[15] + model[1].items.loc[1])

    # second item + user item
    preds = algo.predict(model, 12, [2])
    assert preds.loc[2] == approx(model[1].mean + model[1].users.loc[12] + model[1].items.loc[2])

    # blended
    preds = algo.predict(model, 10, [1, 5])
    assert preds.loc[1] == 4.0
    assert preds.loc[5] == approx(model[1].mean + model[1].users.loc[10] + model[1].items.loc[5])

    # blended unknown
    preds = algo.predict(model, 10, [5, 1, -23081])
    assert len(preds) == 3
    assert preds.loc[1] == 4.0
    assert preds.loc[5] == approx(model[1].mean + model[1].users.loc[10] + model[1].items.loc[5])
    assert preds.loc[-23081] == approx(model[1].mean + model[1].users.loc[10])


def test_topn_recommend():
    pred = basic.Memorized(simple_df)
    rec = basic.TopN(pred)

    rec10 = rec.recommend(None, 10, candidates=[1, 2])
    assert all(rec10.item == [2, 1])
    assert all(rec10.score == [5, 4])

    rec2 = rec.recommend(None, 12, candidates=[1, 2])
    assert len(rec2) == 1
    assert all(rec2.item == [1])
    assert all(rec2.score == [3])

    rec10 = rec.recommend(None, 10, n=1, candidates=[1, 2])
    assert len(rec10) == 1
    assert all(rec10.item == [2])
    assert all(rec10.score == [5])


def test_popular():
    algo = basic.Popular()
    model = algo.train(lktu.ml_pandas.renamed.ratings)
    counts = lktu.ml_pandas.renamed.ratings.groupby('item').user.count()
    counts = counts.nlargest(100)

    assert model is not None
    assert model.max() == counts.max()

    recs = algo.recommend(model, 2038, 100)
    assert len(recs) == 100
    assert all(np.diff(recs.score) <= 0)

    assert recs.score.iloc[0] == counts.max()
    # the 10 most popular should be the same
    assert all(counts.index[:10] == recs.item[:10])


def test_pop_candidates():
    algo = basic.Popular()
    model = algo.train(lktu.ml_pandas.renamed.ratings)
    counts = lktu.ml_pandas.renamed.ratings.groupby('item').user.count()
    items = lktu.ml_pandas.renamed.ratings.item.unique()

    assert model is not None
    assert model.max() == counts.max()

    candidates = np.random.choice(items, 500, replace=False)

    recs = algo.recommend(model, 2038, 100, candidates)
    assert len(recs) == 100
    assert all(np.diff(recs.score) <= 0)

    ccs = counts.loc[candidates]
    ccs = ccs.sort_values(ascending=False)

    assert recs.score.iloc[0] == ccs.max()
    equiv = ccs[ccs == ccs.max()]
    assert recs.item.iloc[0] in equiv.index


def test_pop_save_load(tmp_path):
    tmp_path = lktu.norm_path(tmp_path)
    algo = basic.Popular()
    original = algo.train(lktu.ml_pandas.renamed.ratings)

    fn = tmp_path / 'pop.mod'
    algo.save_model(original, fn)

    model = algo.load_model(fn)
    assert model is not original

    counts = lktu.ml_pandas.renamed.ratings.groupby('item').user.count()
    counts = counts.nlargest(100)

    assert model is not None
    assert model.max() == counts.max()

    recs = algo.recommend(model, 2038, 100)
    assert len(recs) == 100
    assert all(np.diff(recs.score) <= 0)

    assert recs.score.iloc[0] == counts.max()
    # the 10 most popular should be the same
    assert all(counts.index[:10] == recs.item[:10])


def test_random():
    # test case: no seed
    algo = basic.Random()
    model = algo.train(lktu.ml_pandas.renamed.ratings)
    items = lktu.ml_pandas.renamed.ratings['item'].unique()
    users = lktu.ml_pandas.renamed.ratings['user'].unique()
    nitems = len(items)
    nusers = len(users)

    assert model is not None

    recs1 = algo.recommend(model, 2038, 100)
    recs2 = algo.recommend(model, 2028, 100)
    assert len(recs1) == 100
    assert len(recs2) == 100
    # with very high probabilities
    assert set(recs1['item']) != set(recs2['item'])

    recs_all = algo.recommend(model, 2038)
    assert len(recs_all) == nitems
    assert set(items) == set(recs_all['item'])

    # test case: one single seed
    algo = basic.Random(10)
    model = algo.train(lktu.ml_pandas.renamed.ratings)

    assert model is not None

    # when different users having the same random seed,
    # then recommendations should be the same.
    recs1 = algo.recommend(model, 2038, 100)
    recs2 = algo.recommend(model, 2028, 100)
    assert len(recs1) == 100
    assert set(recs1['item']) == set(recs2['item'])

    recs1 = algo.recommend(model, 2038)
    recs2 = algo.recommend(model, 2028)
    assert len(recs1) == nitems
    assert np.array_equal(recs1['item'].values, recs2['item'].values)

    # test case: seeds Series
    seeds = pd.Series(range(nusers), index=users)
    algo = basic.Random(seeds)
    model1 = algo.train(lktu.ml_pandas.renamed.ratings)
    # same seeds with a second run
    model2 = algo.train(lktu.ml_pandas.renamed.ratings)

    assert model1 is not None
    assert model2 is not None

    # get two different users from all users
    user1, user2 = np.random.choice(users, size=2, replace=False)
    recs1 = algo.recommend(model1, user1, 100)
    recs2 = algo.recommend(model1, user2, 100)
    assert len(recs1) == 100
    assert len(recs2) == 100
    assert set(recs1['item']) != set(recs2['item'])
    recs3 = algo.recommend(model2, user1, 100)
    recs4 = algo.recommend(model2, user2, 100)
    assert len(recs3) == 100
    assert len(recs4) == 100
    assert set(recs3['item']) != set(recs4['item'])
    # consistency between two runs
    assert set(recs1['item']) == set(recs3['item'])
    assert set(recs2['item']) == set(recs4['item'])

    # recommend from candidates
    candidates = np.random.choice(items, 500, replace=False)
    recs1 = algo.recommend(model1, user1, 100, candidates=candidates)
    recs2 = algo.recommend(model1, user2, 100, candidates=candidates)
    assert len(recs1) == 100
    assert len(recs2) == 100
    assert set(recs1['item']) != set(recs2['item'])
    recs3 = algo.recommend(model2, user1, 100, candidates=candidates)
    recs4 = algo.recommend(model2, user2, 100, candidates=candidates)
    assert len(recs3) == 100
    assert len(recs4) == 100
    assert set(recs3['item']) != set(recs4['item'])
    # consistency between two runs
    assert set(recs1['item']) == set(recs3['item'])
    assert set(recs2['item']) == set(recs4['item'])
