import numpy as np


from scipy.spatial import ConvexHull


def vertices(x,y):
    dx=[0,0,1,1]
    dy=[0,1,1,0]
    xy=[]
    for ddx,ddy in zip(dx,dy):
        xx=x+ddx
        yy=y+ddy
        xy.extend(list(zip(xx,yy)))
    xy=np.array(list(set(xy)))

    hull=ConvexHull(xy)
    
    xh,yh=[],[]
    for vertex in hull.vertices:
        xh.append(xy[vertex,0])
        yh.append(xy[vertex,1])
    xh,yh=np.array(xh),np.array(yh)

    return xh,yh
    
