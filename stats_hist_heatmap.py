# -*- coding:utf-8 -*-
import numpy as np
import pandas as pd
import matplotlib as mpl
from datetime import *
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from scipy import stats
from astropy.convolution.kernels import Gaussian2DKernel
from astropy.convolution import convolve, Gaussian1DKernel
import requests
import time

xmin = 116.0
xmax = 116.8
ymin = 39.6
ymax = 40.25


def read_data(excelfile, filt=True):
    print("Reading data:{}".format(excelfile))
    df = pd.read_excel(excelfile)
    mask = df[(df["lng"] > 118) | (df["lat"] < 39.4)]
    df.drop(index=mask.index, inplace=True, axis=1)
    if filt:
        df = df[
            (df["lng"] >= xmin)
            & (df["lng"] <= xmax)
            & (df["lat"] >= ymin)
            & (df["lat"] <= ymax)
        ]
    print("Data reading finished!")
    return df


def get_address(lon, lat):
    gaode_ak = "e9d8823cabd80c4f62135f82c88fdf75"
    gaode_api = (
        "http://restapi.amap.com/v3/geocode/"
        "regeo?output=json&"
        "location={},{}&key={}&"
        "radius=1000&extensions=all"
    ).format(lon, lat, gaode_ak)
    response = requests.get(gaode_api).json()
    if response.get("status") == "0":
        print(" 查询错误，Info:", response.get("info"))
        return ""
    else:
        address = response.get("regeocode")["formatted_address"]
        township = response.get("regeocode").get("addressComponent")["township"]
        towncode = response.get("regeocode").get("addressComponent")["towncode"]
        return (address, township, towncode)


def cal_hist(df, bins, filt=True):
    if filt:
        lonlat_range = [[xmin, xmax], [ymin, ymax]]
    else:
        lon = df["lng"]
        lat = df["lat"]
        lonlat_range = [[lon.min(), lon.max()], [lat.min(), lat.max()]]
        print("range:", lonlat_range)
    hist, xedges, yedges = np.histogram2d(
        x=np.array(df.lng), y=np.array(df.lat), bins=[bins, bins], range=lonlat_range
    )
    hist = hist.T
    dfhist = pd.DataFrame(hist)
    dfhist.to_csv("distribution_2d_histogram_{}.csv".format(bins))
    with open(
        "logistics_service_lon_lat_hist_{}_{}_{}.csv".format(
            bins, date.today().month, date.today().day
        ),
        "w",
        encoding="utf-8",
    ) as f:
        f.write("j,i,lat,long,counts,address,township,towncode\n")
        for j, y in enumerate(yedges[:-1]):
            for i, x in enumerate(xedges[:-1]):
                if hist[j][i] <= 0.0:
                    continue
                mid_x = (xedges[i + 1] + x) / 2
                mid_y = (yedges[j + 1] + y) / 2
                # mid_x = x
                # mid_y = y
                address, township, towncode = get_address(mid_x, mid_y)
                str_info = ",".join(
                    map(
                        str,
                        [j, i, mid_y, mid_x, hist[j][i], address, township, towncode],
                    )
                )
                print(str_info)
                f.write(str_info)
                f.write("\n")
                time.sleep(1)
    f.close()
    return


def smooth_heatmap(df, group_bins=100):
    X = np.array(df.wgs_lon)
    Y = np.array(df.wgs_lat)
    bins_list = [group_bins, group_bins]
    print("bins list", bins_list)
    heatmap, xedges, yedges = np.histogram2d(
        x=X, y=Y, bins=bins_list, range=[[xmin, xmax], [ymin, ymax]]
    )
    fig, ax = plt.subplots(1, 1)
    ax.plot(df.wgs_lon, df.wgs_lat, ".", markersize=3, alpha=0.02, color="#8B8B83")
    conv_z = convolve(np.rot90(heatmap), Gaussian2DKernel(stddev=5))
    pd.DataFrame(conv_z).to_csv("convolve_matrix_{}.csv".format(group_bins))
    cs = ax.imshow(conv_z, cmap=cm.RdYlGn_r, extent=[xmin, xmax, ymin, ymax])
    cx, cy, cz = gauss_kde_filt(df, group_bins * (1j))
    ax.contour(cx, cy, cz, cmap=cm.hot_r, linewidths=2)
    cb = plt.colorbar(cs)
    labels = np.linspace(start=0, stop=cz.max() + 1, num=9, endpoint=True)
    loc = np.linspace(-1, 4, 10, endpoint=True)
    cb.set_ticks(loc)
    cb.set_ticklabels(labels)
    plt.title("Max density of logistics service {}".format(int(cz.max())))
    plt.savefig("beijing_logistics_service_convolve.png")
    plt.show()


def gauss_kde_filt(dfcopy, bins):

    X, Y = np.mgrid[xmin:xmax:bins, ymin:ymax:bins]
    positions = np.vstack([X.ravel(), Y.ravel()])

    m1 = np.array(dfcopy["wgs_lon"])
    m2 = np.array(dfcopy["wgs_lat"])
    values = np.vstack([m1, m2])
    kernel = stats.gaussian_kde(values)
    Z = np.reshape(kernel(positions).T, X.shape)
    Z[Z < 0.0001] = 0.0
    return (X, Y, Z)


def draw_heatmap(df, X, Y, Z):
    fig, ax = plt.subplots(figsize=(18, 10))
    # fig.set_size_inches(18, 10)
    ax.plot(df.wgs_lon, df.wgs_lat, ".", markersize=5, alpha=0.5, color="#8B8B83")
    cs = ax.imshow(np.rot90(Z), cmap=cm.RdYlGn_r, extent=[xmin, xmax, ymin, ymax])

    cb = plt.colorbar(cs)
    labels = np.arange(start=0, stop=Z.max() * 1.2, step=Z.max() / 10).round(2)
    loc = [11 * x / Z.max() for x in labels]
    cb.set_ticks(loc)
    cb.set_ticklabels(labels)

    # plt.gca().invert_yaxis()
    ax.contour(X, Y, Z, cmap=cm.hot_r, linewidths=2)
    ax.set_xlim([xmin, xmax])
    ax.set_ylim([ymin, ymax])
    plt.title("The distribution service heatmap in Beijing")
    plt.savefig("beijing_logistics_heatmap.png", dpi=200)
    plt.show()


if __name__ == "__main__":
    print("开始计算高斯滤波数据....\n")
    df = read_data(u"1711 - 整理完成.xlsx")
    cal_hist(df, 50, filt=False)
    # smooth_heatmap(df, group_bins=100)
    # X,Y,Z = gauss_kde_filt(df,300j)
    # draw_heatmap(df, X, Y, Z)
    # print(f'max value:{Z.max()}')
    print("计算结束!")
