import root_numpy
import pandas
import numpy as np
from math import log

signalMap = {
              "DM30" : ["T2DegStop_250_220", 
                        "T2DegStop_275_245", 
                        "T2DegStop_300_270", 
                        "T2DegStop_325_295", 
                        "T2DegStop_350_320", 
                        "T2DegStop_375_345", 
                        "T2DegStop_400_370", 
                        "T2DegStop_425_395", 
                        "T2DegStop_450_420", 
                        "T2DegStop_475_445", 
                        "T2DegStop_500_470", 
                        "T2DegStop_525_495", 
                        "T2DegStop_550_520", 
                        "T2DegStop_575_545", 
                        "T2DegStop_600_570", 
                        "T2DegStop_625_595", 
                        "T2DegStop_650_620", 
                        "T2DegStop_675_645", 
                        "T2DegStop_700_670", 
                        "T2DegStop_725_695", 
                        "T2DegStop_750_720", 
                        "T2DegStop_775_745", 
                        "T2DegStop_800_770"],
              "300_270" : ["T2DegStop_300_270"],
              "550_520" : ["T2DegStop_550_520"]
            }
bkgDatasets = [
                "Wjets_70to100",
                "Wjets_100to200",
                "Wjets_200to400",
                "Wjets_400to600",
                "Wjets_600to800",
                "Wjets_800to1200",
                "Wjets_1200to2500",
                "Wjets_2500toInf",
                "TTJets_DiLepton",
                "TTJets_SingleLeptonFromTbar",
                "TTJets_SingleLeptonFromT",
                "ZJetsToNuNu_HT100to200",
                "ZJetsToNuNu_HT200to400",
                "ZJetsToNuNu_HT400to600",
                "ZJetsToNuNu_HT600to800",
                "ZJetsToNuNu_HT800to1200",
                "ZJetsToNuNu_HT1200to2500",
                "ZJetsToNuNu_HT2500toInf"
              ]


def StopDataLoader(path, features, test="550_520", selection="", treename="bdttree", suffix="", signal="DM30", fraction=1.0):
  if signal not in signalMap:
    raise KeyError("Unknown training signal requested ("+signal+")")
  if test not in signalMap:
    raise KeyError("Unknown test signal requested ("+test+")")
  if fraction >= 1.0:
    fraction = 1.0
  if fraction < 0.0:
    raise ValueError("An invalid fraction was chosen")
  if "XS" not in features:
    features.append("XS")
  if "weight" not in features:
    features.append("weight")

  sigDev = None
  sigVal = None
  
  
  for sigName_test in signalMap[test]:
    tmp = root_numpy.root2array(
                                path + "test/" + sigName_test + suffix + ".root",
                                treename=treename,
                                selection=selection,
                                branches=features
                                )
    if fraction < 1.0:
      tmp = tmp[:int(len(tmp)*fraction)]
    if sigVal is None:
      sigVal = pandas.DataFrame(tmp)
    else:
      sigVal = sigVal.append(pandas.DataFrame(tmp), ignore_index=True)
    

  for sigName in signalMap[signal]:
    tmp = root_numpy.root2array(
                                path + "train/" + sigName + suffix + ".root",
                                treename=treename,
                                selection=selection,
                                branches=features
                                )
    if fraction < 1.0:
      tmp = tmp[:int(len(tmp)*fraction)]
    if sigDev is None:
      sigDev = pandas.DataFrame(tmp)
    else:
      sigDev = sigDev.append(pandas.DataFrame(tmp), ignore_index=True)



  bkgDev = None
  bkgVal = None
  for bkgName in bkgDatasets:
    tmp = root_numpy.root2array(
                                path + "/train/" + bkgName + suffix + ".root",
                                treename=treename,
                                selection=selection,
                                branches=features
                                )
    if fraction < 1.0:
      tmp = tmp[:int(len(tmp)*fraction)]
    if bkgDev is None:
      bkgDev = pandas.DataFrame(tmp)
    else:
      bkgDev = bkgDev.append(pandas.DataFrame(tmp), ignore_index=True)

    tmp = root_numpy.root2array(
                                path + "/test/" + bkgName + suffix + ".root",
                                treename=treename,
                                selection=selection,
                                branches=features
                                )
    if fraction < 1.0:
      tmp = tmp[:int(len(tmp)*fraction)]
    if bkgVal is None:
      bkgVal = pandas.DataFrame(tmp)
    else:
      bkgVal = bkgVal.append(pandas.DataFrame(tmp), ignore_index=True)

  sigDev["category"] = 1
  sigVal["category"] = 1
  bkgDev["category"] = 0
  bkgVal["category"] = 0
  sigDev["sampleWeight"] = 1
  sigVal["sampleWeight"] = 1
  bkgDev["sampleWeight"] = 1
  bkgVal["sampleWeight"] = 1

  if fraction < 1.0:
    sigDev.weight = sigDev.weight/fraction
    sigVal.weight = sigVal.weight/fraction
    bkgDev.weight = bkgDev.weight/fraction
    bkgVal.weight = bkgVal.weight/fraction

  sigDev.sampleWeight = sigDev.weight/sigDev.XS
  sigVal.sampleWeight = sigVal.weight/sigVal.XS
  bkgDev.sampleWeight = bkgDev.weight
  bkgVal.sampleWeight = bkgVal.weight

  sigDev.sampleWeight = sigDev.sampleWeight/sigDev.sampleWeight.sum()
  sigVal.sampleWeight = sigVal.sampleWeight/sigVal.sampleWeight.sum()
  bkgDev.sampleWeight = bkgDev.sampleWeight/bkgDev.sampleWeight.sum()
  bkgVal.sampleWeight = bkgVal.sampleWeight/bkgVal.sampleWeight.sum()

  dev = sigDev.copy()
  dev = dev.append(bkgDev.copy(), ignore_index=True)
  val = sigVal.copy()
  val = val.append(bkgVal.copy(), ignore_index=True)
  return dev, val
  
def FOM1(sIn, bIn):
    s, sErr = sIn
    b, bErr = bIn
    fom = s / (b**0.5)
    fomErr = ((sErr / (b**0.5))**2+(bErr*s / (2*(b)**(1.5)) )**2)**0.5
    return (fom, fomErr)

def FOM2(sIn, bIn):
    s, sErr = sIn
    b, bErr = bIn
    fom = s / ((s+b)**0.5)
    fomErr = ((sErr*(2*b + s)/(2*(b + s)**1.5))**2  +  (bErr * s / (2*(b + s)**1.5))**2)**0.5
    return (fom, fomErr)

def FullFOM(sIn, bIn, fValue=0.2):
    s, sErr = sIn
    b, bErr = bIn
    fomErr = 0.0 # Add the computation of the uncertainty later
    fomA = 2*(s+b)*log(((s+b)*(b + (fValue*b)**2))/(b**2 + (s + b) * (fValue*b)**2))
    fomB = log(1 + (s*b*b*fValue*fValue)/(b*(b+(fValue*b)**2)))/(fValue**2)
    fom = (fomA - fomB)**0.5
    return (fom, fomErr)

def getYields(dataVal, cut=0.5, luminosity=35866, splitFactor=2):
    #defines the selected test data 
    selectedVal = dataVal[dataVal.NN>cut]
            
    #separates the true positives from false negatives
    selectedSig = selectedVal[selectedVal.category == 1]
    selectedBkg = selectedVal[selectedVal.category == 0]
            
    sigYield = selectedSig.weight.sum()
    sigYieldUnc = np.sqrt(np.sum(np.square(selectedSig.weight)))
    bkgYield = selectedBkg.weight.sum()
    bkgYieldUnc = np.sqrt(np.sum(np.square(selectedBkg.weight)))

    sigYield = sigYield * luminosity * splitFactor          #The factor 2 comes from the splitting
    sigYieldUnc = sigYieldUnc * luminosity * splitFactor
    bkgYield = bkgYield * luminosity * splitFactor
    bkgYieldUnc = bkgYieldUnc * luminosity * splitFactor

    return ((sigYield, sigYieldUnc), (bkgYield, bkgYieldUnc))
