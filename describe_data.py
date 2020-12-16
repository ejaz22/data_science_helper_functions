import numpy as np
import pandas as pd
from pandas.api.types import CategoricalDtype


def display_all(df, rows=10, columns=1000):
    """
    :param df: Pandas DataFrame
    :param rows: Max Number of rows to print
    :param columns: Max Number of columns to print
    """
    with pd.option_context("display.max_rows", rows, "display.max_columns", columns):
        print(df)


def auto_set_type(df, type_dict):
    """
    :param df: Pandas DataFrame
    :param type_dict: Dictionary of column name and type to format to in the format:
            {'month': CategoricalDtype(categories=range(1,13))}
            ** Only necessary for Categorical & Boolean Columns **
    :return: Pandas DataFrame
    """
    for col in type_dict:
        df[col] = df[col].astype(type_dict[col])

    return df


def auto_dates(df, date_name='date', time=False):
    """
    :param df: Pandas DataFrame
    :param date_name: Only needed if index is not DatetimeIndex type.
                        String: Name of date column in df
    :param time: Set to True if time part is necessary
    :return: Pandas DataFrame
    """
    T = df.index.to_series() if isinstance(df.index, pd.DatetimeIndex) else pd.to_datetime(df[date_name])

    if time:
        df['hour'] = T.dt.hour
        df['minute'] = T.dt.minute
        df['second'] = T.dt.second
    df['year'] = T.dt.year
    df['month'] = T.dt.month.astype(CategoricalDtype(categories=range(1, 13)))
    df['week'] = T.dt.weekofyear.astype(CategoricalDtype(categories=range(1, 54)))
    df['day'] = T.dt.day.astype(CategoricalDtype(categories=range(1, 32)))
    df['dow'] = T.dt.dayofweek.astype(CategoricalDtype(categories=range(0, 7)))
    df['doy'] = T.dt.dayofyear.astype(CategoricalDtype(categories=range(0, 366)))
    df['start_month'] = T.dt.is_month_start.astype('int')
    df['end_month'] = T.dt.is_month_end.astype('int')
    df['start_quarter'] = T.dt.is_quarter_start.astype('int')
    df['end_quarter'] = T.dt.is_quarter_end.astype('int')
    df['start_year'] = T.dt.is_year_start.astype('int')
    df['end_year'] = T.dt.is_year_end.astype('int')
    df['n_day_in_month'] = T.dt.days_in_month
    return df


def auto_remove_novariance(df):
    """
    :param df: Pandas DataFrame
    :return: Pandas DataFrame
    """
    uniques = df.apply(pd.Series.nunique)
    return df.drop(columns=list(uniques[uniques == 1].index))


def auto_dummies(df):
    """
    :param df: Pandas DataFrame
    :return: Pandas Dataframe()
    """
    return pd.get_dummies(df, columns=list(df.select_dtypes(include='category').columns), drop_first=True)


def get_category_size(df, max_cat=50):
    cat = df.select_dtypes(include='category').columns
    return [(c, len(df[c].cat.categories), min(max_cat, len(df[c].cat.categories) // 2)) for c in cat]


def sort_columns(df, reverse=False):
    return df[sorted(df.columns, reverse=reverse)]





"""
This function performs several analysis on passed dataframe.
dependency : tabulate module
"""

def describe_data(df,target_var=None):
    
    """
    this function takes pandas dataframe as an argument
    and returns several analysis on dataset 
    """
    if df.__class__.__name__ != 'DataFrame':
            raise Exception('Error: object is not a pandas DataFrame.')
            
    
    # set display of numbers
    pd.set_option('precision', 2)
    pd.options.display.float_format = "{:,.2f}".format
    
    # dataset dimensions
    print("1. The dataset has {} records and {} columns".format(df.shape[0],df.shape[1]),end='\n\n\n')
    
    # describe missing, unique and data_types
    print("2. Columns details: ",end='\n\n')
    summ = pd.DataFrame(df.dtypes,columns=['Data_Types'])
    summ = summ.reset_index()
    summ['Columns'] = summ['index']
    summ = summ[['Columns','Data_Types']]
    summ['Missing'] = df.isnull().sum().values    
    summ['Uniques'] = df.nunique().values
    print(summ.to_markdown(showindex=False,floatfmt=('.2f')), end='\n\n\n')
    
    
    # null values analysis
    print("3. Null values analysis:",end='\n\n')
    nulls = df.isnull().sum()
    nulls = nulls[df.isnull().sum()>0].sort_values(ascending=False)
    nulls_report = pd.concat([nulls, nulls / df.shape[0]], axis=1, keys=['Missing_Values','Missing_Ratio'])
    if nulls_report.empty:
        print('The dataset has no null values',end='\n\n\n')
    else:
        print(nulls_report,end='\n\n\n')
    
    # describe stats
    print("4. Statistics:",end='\n\n')
    stat = df.describe().T
    print(stat.to_markdown(floatfmt=('.2f')),end='\n\n\n')
    
    # Correlation analysis(pearson)
    print("5. Correlation Analysis (pearson)",end='\n\n')
    corr = df.corr(method ='pearson')
    print(corr.to_markdown(floatfmt=('.2f')),end='\n\n\n')

    
    import numpy as np
from sklearn import metrics
from sklearn.metrics.classification import _check_targets
import matplotlib.pyplot as plt


def multiclass_auc(gt, preds):
    """
    Compute a class-weighted multiclass AUC, as defined in section 9.2 of [1].
    Parameters
    ----------
    gt : sequence
        A 1D vector of ground truth class labels
    preds : array
        An array of classifier predictions, where columns correspond to classes
        and rows to data instances.
    [1] https://ccrma.stanford.edu/workshops/mir2009/references/ROCintro.pdf
    """
    assert gt.shape[0] == preds.shape[0]
    assert gt.max() < preds.shape[1]

    # compute AUC for each class in turn
    aucs = []
    weights = []
    for class_id in range(preds.shape[1]):
        class_gt = gt == class_id
        if class_gt.sum() == 0:
            continue
        class_preds = preds[:, class_id]
        aucs.append(metrics.roc_auc_score(class_gt, class_preds))
        weights.append((gt == class_id).sum())

    # return the class-weighted mean of the AUCs
    return np.average(np.array(aucs), weights=np.array(weights))


def class_normalised_accuracy(y_true, y_pred, min_class_count=1,
        accuracy_function=metrics.accuracy_score):
    """
    Compute class-normalised classification accuracy score
    Accuracy done per-class and averaged across all classes.
    This mitigates against the effect of large class imbalance in the test
    set (see e.g. [1]). However, it can make evaluation sensistive to changes
    in classification on very infrequent classes - you can use min_class_count
    to deal with this.
    Parameters
    ----------
    y_true : array
        Integers representing ground truth class labels
    y_pred : array
        Integers representing predicted labels, or array of probabilities
    min_class_count : integer, optional
        Ground truth classes with fewer than this number of items in them
        are ignored in the final computation.
    accuracy_function : function
        A function which accepts (y_true, y_pred) as arguments and returns
        a scalar accuracy score. By default, is simply the fraction of
        classes correct, as implemented by metrics.accuracy_score.
        However, could be top5 accuracy etc. e.g.:
        >>> from ml_helpers import evaluation
        >>> from functools import partial
        >>> top2 = partial(evaluation.top_n_accuracy, n=2)
        >>> ground_truth = [1, 2, 2]
        >>> preds = np.array([[0.2, 0.8, 0.0],
                              [0.0, 0.6, 0.4],
                              [0.0, 0.0, 1.0]])
        >>> evaluation.class_normalised_accuracy(
                ground_truth, preds, accuracy_function=top2)
    [1] Gabriel J. Brostow, Jamie Shotton, Julien Fauqueur and Roberto Cipolla
    Segmentation and Recognition using Structure from Motion Point Clouds
    """
    y_true = np.asarray(y_true)
    assert y_true.shape[0] == y_pred.shape[0]

    # for sklearn, we can't have y_true as an integer list if y_pred is array
    if y_pred.ndim == 2 and accuracy_function == metrics.accuracy_score:
        y_pred = np.argmax(y_pred, axis=1)

    accs = []
    for target in np.unique(y_true):
        idxs = y_true == target

        # only include if we have enough ground truth classes
        if idxs.sum() >= min_class_count:
            accs.append(accuracy_function(y_true[idxs], y_pred[idxs]))

    return np.mean(accs)


def plot_roc_curve(gt, pred, label="", plot_midpoint=True):
    """
    Plot a single roc curve, optionally with a dot at the 0.5 threshold
    """

    # evaluating and finding the curve midpoint
    fpr, tpr, thresh = metrics.roc_curve(gt, pred.ravel())
    roc_auc = metrics.auc(fpr, tpr)

    # plotting curve
    plt.plot(fpr, tpr, label='%s (area = %0.2f)' % (label, roc_auc))

    if plot_midpoint:
        mid_idx = np.argmin(np.abs(thresh-0.5))
        plt.plot(fpr[mid_idx], tpr[mid_idx], 'bo')

    # labels and legends
    plt.legend(loc='best')
    plt.xlabel('FPR')
    plt.ylabel('TPR')


def top_n_accuracy(y_true, y_pred, n, summarize=True):
    """
    Computes the fraction of items which have the correct answer in the top
    n predictions made by a classifier.
    Parameters
    ----------
    y_true : array
        Integers representing ground truth class labels
    y_pred : array
        Matrix representing class probabilities as predicted by a classifer
    n : integer
        If the ground truth is in the top n prediction of the classifier,
        the item is counted as a successful prediction
    """
    assert len(y_true) == y_pred.shape[0]
    assert max(y_true) < y_pred.shape[1]

    y_pred_sorted = np.argsort(y_pred, axis=1)[:, ::-1][:, :n]

    successes = [gt in pred for pred, gt in zip(y_pred_sorted, y_true)]

    if summarize:
        return np.mean(successes)
    else:
        return successes


def plot_confusion_matrix(y_true, y_pred, title='Confusion matrix',
        cls_labels=None, cmap=plt.cm.Blues, normalise=False, grid=True):
    """
    Plot a confusion matrix using matplotlib. The matrix is computed using
    sklearn.metrics.confusion_matrix. Rows are ground truth labels; columns are
    predictions.
    Code adapted from:
    http://scikit-learn.org/stable/auto_examples/model_selection/plot_confusion_matrix.html
    Parameters
    ----------
    y_true : array
        Integers representing ground truth class labels
    y_pred : array
        Either an array of classifier predictions, where columns correspond
        to classes and rows to data instances, or an array of size of y_true
        where each integer represents predicted class label
    title : string, optional
        Title to be provided for the plot
    cls_labels : list, optional
        A list of strings to use as the tick labels.
    cmap : matplotlib colourmap, optional
        Colourmap used for the plot
    normalise : boolean, optional
        If true, each row is normalised to sum to one. Otherwise, each entry in
        confusion matrix is an integer.
    grid : boolean, options
        If true, plots a faint grey grid on the confusion matrix image.
        This is offset 0.5 from standard tick points, so we don't use
        matplotlib ticks here.
    """
    if y_pred.ndim == 2:
        y_pred = np.argmax(y_pred, axis=1)

    # compute confusion matrix
    if cls_labels is not None:
        # this is useful if not all classes are present in y_true/y_pred
        cm = metrics.confusion_matrix(y_true, y_pred, range(len(cls_labels)))
    else:
        cm = metrics.confusion_matrix(y_true, y_pred)
    N = cm.shape[0]

    if normalise:
        cm = cm.astype(float)
        cm /= cm.sum(axis=1, keepdims=True)

    # plotting and formatting plot
    plt.clf()
    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar(fraction=0.046, pad=0.04)

    if cls_labels is not None:
        tick_marks = np.arange(len(cls_labels))
        plt.xticks(tick_marks, cls_labels, rotation=90)
        plt.yticks(tick_marks, cls_labels)

    if normalise:
        plt.clim(0.0, 1.0)

    if grid:
        # remove standard ticks
        plt.tick_params(axis='x', which='both', bottom='off', top='off')
        plt.tick_params(axis='y', which='both', left='off', right='off')

        # add grid
        params = {'color': [0.8, 0.8, 0.8], 'linewidth': 1}
        for row in range(N-1):
            plt.plot((-0.5, N), (row + 0.5, row + 0.5), **params)
            plt.plot((row + 0.5, row + 0.5), (-0.5, N), **params)

    plt.tight_layout()

    plt.ylabel('True label')
    plt.xlabel('Predicted label')

    plt.xlim(-0.5, float(N) - 0.5)
    plt.ylim(float(N) - 0.5, -0.5)

    if normalise:
        plt.clim(0, 1.0)
