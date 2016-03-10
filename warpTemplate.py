# -*- coding: utf-8 -*-
"""
Created on Wed Jan 06 21:09:02 2016

@author: 开圣
"""
import urllib
from json import *
import os
import numpy as np
from PIL import Image,ImageDraw
from OBJ import obj
#face++ api
from facepp import API,File
API_KEY = "b068f469bf92bbf202a2a351093f81c3"
API_SECRET = "-OmBhNOBMEhWYpk6jll-0n4zNEReAzrm"
api = API(API_KEY,API_SECRET)

def landmarkFromFacepp(imgPath):
    infor = api.detection.detect(img = File(imgPath))
    try:
        faceID = infor[u'face'][0][u'face_id']
    except:
        print ("no face detected")
    req_url = "http://api.faceplusplus.com/detection/landmark"
    params = urllib.urlencode({'api_secret':API_SECRET,'api_key':API_KEY,'face_id':faceID,'type':'83p'})
    req_rst = urllib.urlopen(req_url,params).read() # landmark data
    req_rst_dict = JSONDecoder().decode(req_rst)
    if len(req_rst_dict['result']) == 1:
        landmarkDict = req_rst_dict['result'][0]['landmark']
    imgInfo = Image.open(imgPath)
    xSize = imgInfo.size[0]
    ySize = imgInfo.size[1]
    landmarkList = sorted(list(landmarkDict))
    landmark_array = []
    for key in landmarkList:
        temp_xy = [landmarkDict[key]['x'],landmarkDict[key]['y']]
        landmark_array.append(np.array(temp_xy))
    landmarkArray = np.array(landmark_array)
    landmarkArray[:,0] = landmarkArray[:,0] * xSize / 100
    landmarkArray[:,1] = landmarkArray[:,1] * ySize / 100
    return landmarkArray

#calculate cot for L
def calCot(vec1, vec2):
    cos = vec1.dot(vec2)/(np.sqrt(vec1.dot(vec1))*np.sqrt(vec2.dot(vec2)))
    sin = np.sqrt(1 - cos**2)
    cot = cos/sin
    return cot

# calculate L
def calL(obj):
    ptsNum = len(obj.v)
    L = np.zeros((3*ptsNum, 3*ptsNum))
    for face in obj.face:
        p = map(np.array, map(lambda x:obj.v[x], face))
        for i in range(3):
            for j in range(3):
                if i != j:
                    k = 3 - i -j
                    if L[3*face[i], 3*face[j]] == 0:
                        val = calCot(p[k]-p[i], p[k]-p[j])
                        L[3*face[i], 3*face[j]] = val
                        L[3*face[i]+1, 3*face[j]+1] = val
                        L[3*face[i]+2, 3*face[j]+2] = val
                    else:
                        val = 0.5 * (calCot(p[k]-p[i], p[k]-p[i]) + L[3*face[i], 3*face[j]])
                        L[3*face[i], 3*face[j]] = val
                        L[3*face[i]+1, 3*face[j]+1] = val
                        L[3*face[i]+2, 3*face[j]+2] = val
    return L

# calculate P (weakly perspective)    
def calP(landmark2D, landmark3D):
    b1 = landmark2D[:,0]
    b2 = landmark2D[:,1]
    A = np.c_[landmark3D, np.ones((len(landmark3D), 1))]
    #import pdb
    #pdb.set_trace()
    m1 = np.linalg.lstsq(A, b1)[0]
    m2 = np.linalg.lstsq(A, b2)[0]
    P = np.c_[m1, m2, np.array([0,0,0,1])]
    return P.T

    
def drawL(imgPath, landmark):
    img = Image.open(imgPath)
    imDraw = ImageDraw.Draw(img)
    radius = 10
    for p in landmark:
        x = p[0]
        y = p[1]
        imDraw.ellipse((x - radius,y -radius,x + radius, y + radius), fill = 'red', outline = 'red')
    return img

#load landmark index    
def loadLandmark(fp):
    text = open(fp, 'r')    
    landmarkIndex = []
    for line in text:
        line = line.split()[0]
        landmarkIndex.append(int(float(line))-1)
    return landmarkIndex

   
if __name__ == '__main__':
    rootDir = r'D:\WinPython-64bit-2.7.10.1\mine\Unconstrained 3D Face Reconstruction\data'
    imgSet = os.path.join(rootDir, 'imgSet')
    landmarkPath = os.path.join(rootDir, 'landmark.txt')
    templatePath = os.path.join(rootDir, 'template.obj')
    template = obj(templatePath)
    template.load()
    L = calL(template)
    vertex = np.array(template.v)
    vCount = len(vertex)
    X0 = vertex.reshape(3*vCount)#3p vector
    landmarkIndex = loadLandmark(landmarkPath)
    landmark3D = vertex[landmarkIndex]
    D = np.zeros((3*vCount, 3*vCount))#selection matrix
    for index in landmarkIndex:
        for i in range(3):
            D[3*index+i, 3*index+i] = 1
    imgList = os.listdir(imgSet)
    Pset = []
    Wset = []
    for im in imgList:
        imgPath = os.path.join(imgSet, im)
        landmark2D = landmarkFromFacepp(imgPath)
        P = calP(landmark2D, landmark3D)
        W = np.zeros((2*vCount,1))
        Pplus = np.zeros((2*vCount, 3*vCount))
        count = 0
        for index in landmarkIndex:
            Pplus[2*index:2*index+2, 2*index:2*index+3] = P[0:2,0:3]
            W[2*index] = landmark2D[count, 0] - P[0, 3]
            W[2*index+1] = landmark2D[count, 1] - P[1, 3]
        Pset.append(Pplus)
        Wset.append(W)
    sumL = L.dot(L)
    sumR = L.dot(L)
    for i in range(len(Pset)):
        sumL = sumL + D.dot(Pset[i].T).dot(Pset[i]).dot(D)
        sumR = sumR + Pset[i].T.dot(Wset[i])
    XX = np.linalg.solve(sumL, sumR)
    

        
            
        
    
    
    
    