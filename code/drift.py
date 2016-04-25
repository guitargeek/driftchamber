"""
This script plots drift velocity against field voltage.
"""

from ROOT import (TFile, TGraph, TF1, AddressOf, TH1F, TCanvas, TGraphErrors,
                  gDirectory, TH1F, gROOT, TLegend, gStyle)
from numpy import array, argmin, mean, zeros, float32, uint32, sqrt
import re
from scipy.stats import sem

gROOT.SetBatch()

# Distance between cathode and signal wires in mm
dist = 95.

# Cut out events with a peak height below a certain threshold,
# because those events were probably triggered by noise
th = 0.02

# the factor between standard deviation and time delta
# obtained from mc with 1e7 muons
factors = array([0.2108, 0.2046, 0.2085, 0.2112])

f = TFile("../data.root")

gStyle.SetPadTickX(1)
gStyle.SetPadTickY(1)

c1 = TCanvas("c1","c1",200,10,500,500)
c1.cd()

hists = []

# Function to calculate a value proportional to the gas amplification for a
# measurement run stored in a tree.
def get_drifttime(treename):
    tree = f.Get(treename)

    widths, starttimes = [], []

    for i, c in enumerate([1, 3, 7, 8]):
        hists.append(TH1F("h_{0}_{1}".format(treename,c), treename+"_{}".format(c), 15, 600, 1600))
        tree.Draw("Chn{1}_Time>>h_{0}_{1}".format(treename,c), "Chn{0}_Height>{1}".format(c, th))

        # TODO: explain why I do this
        widths.append(hists[-1].GetStdDev() / factors[i])
        starttimes.append(hists[-1].GetMean() - widths[-1] / 2)

    width, width_err = mean(widths), sem(widths)
    starttime, starttime_err = mean(starttimes), sem(starttimes)

    return(width, width_err, starttime, starttime_err)

# Initialize lists to store data
voltages, drifttimes, drifttimes_err, starttimes, starttimes_err = [], [], [], [], []

# Get a list of all available tree names
def GetKeyNames( self, dir = "" ):
    self.cd(dir)
    return [key.GetName() for key in gDirectory.GetListOfKeys()]
TFile.GetKeyNames = GetKeyNames

# Calculate the gasamp value for each tree
key_list = f.GetKeyNames("")
for key in key_list:
    numbers = array(re.findall('\d+', key), dtype=int)
    if len(numbers) == 1:
        voltages.append(numbers[0])
        d, de, s, se = get_drifttime(key)
        drifttimes.append(d)
        drifttimes_err.append(de)
        starttimes.append(s)
        starttimes_err.append(se)

# Convert to numpy arrays
voltages = array(voltages, dtype=float)
drifttimes = array(drifttimes, dtype=float)

v_drift = dist/drifttimes
v_drift_err = dist/drifttimes**2*drifttimes_err

##########
# Plotting
##########

fontsize = 0.04

gr = TGraphErrors(len(voltages), voltages/1000/0.1, v_drift*100, zeros(len(voltages)), 1000*v_drift_err)

gr.GetXaxis().SetTitle("Drift field [kV/m]")
gr.GetYaxis().SetTitle("Drift velocity [cm/#mus]")
gr.SetTitle("Drift velocity")

gr.GetYaxis().SetTitleOffset(1.25)

gr.SetMarkerStyle(8)
gr.GetXaxis().SetLabelSize(fontsize)
gr.GetXaxis().SetTitleSize(fontsize)
gr.GetYaxis().SetLabelSize(fontsize)
gr.GetYaxis().SetTitleSize(fontsize)

gr.Draw("AP")

c1.Draw()
c1.Print("../plots/drift.pdf")

f.Close()
