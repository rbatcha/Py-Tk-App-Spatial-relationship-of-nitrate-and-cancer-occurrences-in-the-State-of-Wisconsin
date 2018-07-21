# Author:Roseline Batcha
# GEOG 777 Project 1
# This script explores the relationship between nitrates and cancer
# A GUI is included to assist with the process
# Python version 2.7.10

# Import the system modules
import os
import arcpy
from arcpy import env
from arcpy.sa import *
import arcpy.mapping
from Tkinter import *
from Tkinter import Tk
from PIL import Image, ImageTk
import tkFont
import tkFileDialog
import tkColorChooser
import tkinter
import tkCommonDialog

# Set environment settings
arcpy.env.resamplingMethod = "BILINEAR"
env.workspace = "C:\MyUW\SummerProject1"
arcpy.env.overwriteOutput = True

# Start to build the GUI
root = Tk()
root.title('Spatial Analysis Investigating The Relationship Between Nitrate Levels and Cancer Incidences in Wisconsin')
root.configure(background='Black')
root.resizable(width = FALSE, height = FALSE)


# Setup GUI section for the map
# Make a placeholder image of the WI Census tracts and wells
imagePath = ImageTk.PhotoImage(file="C:\MyUW\SummerProject1\\nwC.JPG")
widgetf = Label(root, image=imagePath, bg="green")
widgetf.pack(side="right", padx=10, pady=10)
Image.ANTIALIAS

## Setup the functions for the GUI##
# Create a function to execute IDW, Zonal Statistics, and OLS. 
def runIDW():
    status['text'] = 'Running IDW on the shapefile...'
    
    # Set environment settings
    arcpy.env.resamplingMethod = "BILINEAR"
    env.workspace = "C:\MyUW\SummerProject1"
    arcpy.env.overwriteOutput = True

    # Set local variables
    inPointFeatures = "well_nitrate.shp"
    zField = "nitr_ran"
    cellSize = ""
    e = float(k.get()) # Convert the string value of the entry box to a float    
    power = e
    print power
    searchRadius = RadiusVariable(10, 150000)

    # Check out the ArcGIS Spatial Analyst extension license
    arcpy.CheckOutExtension("Spatial")

    # Execute IDW
    outIDW = Idw(inPointFeatures, zField, cellSize, power, searchRadius)

    # Save the output 
    outIDW.save("C:\\MyUW\\SummerProject1\\idw1.tif")

    ##
    ### Project the raster from nearest to bilinear - to make it look nice!
    
    
    #setup a new map document for the IDW raster
    mxd = arcpy.mapping.MapDocument(r"C:\\MyUW\\SummerProject1\\idwmap.mxd")
    df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]

    # Make the IDW output a raster layer and add it to the mxd
    # Also give the raster the symbology of an existing layer
    # Add the counties layer and get its symbology as well
    tif = arcpy.mapping.Layer(r"C:\\MyUW\\SummerProject1\\idw1.tif")
    tracts = arcpy.mapping.Layer(r"C:\\MyUW\\SummerProject1\\cancer_tracts.shp")
    idwSymbology = "C:\\MyUW\\SummerProject1\\idw_symbology.lyr"
    tractsSymbology = "C:\\MyUW\\SummerProject1\\cancer_tracts.lyr"
    arcpy.ApplySymbologyFromLayer_management(tif, idwSymbology)
    arcpy.ApplySymbologyFromLayer_management(tracts, tractsSymbology)
    arcpy.mapping.AddLayer(df, tif, "AUTO_ARRANGE")
    arcpy.mapping.AddLayer(df, tracts, "AUTO_ARRANGE")
    
    #mxd.save()    
    
    # Export the mxd to a pdf and a png
    arcpy.mapping.ExportToPDF(mxd, r"C:\\MyUW\\SummerProject1\\Idwmap.pdf")
    arcpy.mapping.ExportToPNG(mxd, r"C:\\MyUW\\SummerProject1\\idwmap.png")    

    status['text'] = 'Success!.., Interpolation (IDW) Complete! PDF  and PNG Exported.'

    # Aggregate the interpolated nitrate locations to
    # the census tract level
    # Run Zonal Statistics as Table on the IDW raster

    status['text'] = 'Running Zonal Statistics as Table...'

    # Set local variables
    inZoneData = "cancer_tracts.shp"
    zoneField = "GEOID10"
    inValueRaster = "idw1.tif"
    outTable = "zonalstattblout02.dbf"

    # Execute ZonalStatisticsAsTable
    outZSaT = ZonalStatisticsAsTable(inZoneData, zoneField, inValueRaster, 
                                     outTable, "NODATA", "MEAN")    

    # Attribute join the Zonal Statistics table to the cancer_tracts table
    try:
        # Set environment settings    
        env.qualifiedFieldNames = False
        
        # Set local variables    
        inFeatures = "cancer_tracts.dbf"
        layerName = "cancer_tracts"
        joinTable = "zonalstattblout02.dbf"
        joinField = "GEOID10"
        expression = ""
        outFeature = "censusjoin"
        isCommon = "KEEP_COMMON"
        
        # Create a feature layer from the vegtype featureclass
        arcpy.MakeFeatureLayer_management (inFeatures,  layerName)
        
        # Join the feature layer to a table
        arcpy.AddJoin_management(layerName, joinField, joinTable, joinField, isCommon)
        
        # Select desired features from veg_layer
        #arcpy.SelectLayerByAttribute_management(layerName, "NEW_SELECTION", expression)
        
        # Copy the layer to a new permanent feature class
        arcpy.CopyFeatures_management(layerName, outFeature)

        status['text'] = 'Success! Zonal Statistics Complete! Attribute features joined.'
        
    except Exception, e:
        # If an error occurred, print line number and error message
        import traceback, sys
        tb = sys.exc_info()[2]
        print "Line %i" % tb.tb_lineno
        print e.message
        
    # Run Regression on the new joined censusjoin shapefile
    # Set property to overwrite existing outputs
    arcpy.env.overwriteOutput = True

    # Local variables...
    workspace = "C:\\MyUW\\SummerProject1"

    try:
        # Set the current workspace (to avoid having to specify the full path to the feature classes each time)
        arcpy.env.workspace = workspace

        # Growth as a function of {log of starting income, dummy for South
        # counties, interaction term for South counties, population density}
        # Process: Ordinary Least Squares... 
        ols = arcpy.OrdinaryLeastSquares_stats("C:\\MyUW\\SummerProject1\\censusjoin.shp", "OID_", 
                            "C:\\MyUW\\SummerProject1\\olsResults.shp", "canrate",
                            "MEAN")   

        # Create Spatial Weights Matrix (Can be based off input or output FC)
        # Process: Generate Spatial Weights Matrix... 
        swm = arcpy.GenerateSpatialWeightsMatrix_stats("C:\\MyUW\\SummerProject1\\censusjoin.shp", "OID_",
                            "C:\\MyUW\\SummerProject1\\euclidean6Neighs.swm",
                            "K_NEAREST_NEIGHBORS",
                            "#", "#", "#", 6) 
                            

        # Calculate Moran's Index of Spatial Autocorrelation for 
        # OLS Residuals using a SWM File.  
        # Process: Spatial Autocorrelation (Morans I)...      
        moransI = arcpy.SpatialAutocorrelation_stats("C:\\MyUW\\SummerProject1\\olsResults.shp", "Residual",
                            "NO_REPORT", "GET_SPATIAL_WEIGHTS_FROM_FILE", 
                            "EUCLIDEAN_DISTANCE", "NONE", "#", 
                            "C:\\MyUW\\SummerProject1\\euclidean6Neighs.swm")

    except:
        # If an error occurred when running the tool, print out the error message.
        print(arcpy.GetMessages())

    # Setup a new map document for the OLS results
    mxdols = arcpy.mapping.MapDocument(r"C:\\MyUW\\SummerProject1\\olsmap.mxd")
    dfols = arcpy.mapping.ListDataFrames(mxdols, "Layers")[0]    

    # Make the OLS output a layer and add it to the mxd
    # Also give the layer the symbology of an existing layer
    olsResults = arcpy.mapping.Layer(r"C:\\MyUW\\SummerProject1\\olsResults.shp")
    olsSymbology = "C:\\MyUW\\SummerProject1\\ols_symbology.lyr"
    arcpy.ApplySymbologyFromLayer_management(olsResults, olsSymbology)
    arcpy.mapping.AddLayer(dfols, olsResults, "AUTO_ARRANGE")

    # Add a legend to the OLS map
    legend = arcpy.mapping.ListLayoutElements(mxdols, "LEGEND_ELEMENT", "Legend")[0]
    legend.autoAdd = True
    legend.adjustColumnCount(1)    

    #mxdols.save()

    # Export the mxd to a pdf
    arcpy.mapping.ExportToPDF(mxdols, "C:\\MyUW\\SummerProject1\\Olsmap.pdf")
    arcpy.mapping.ExportToPNG(mxdols, "C:\\MyUW\\SummerProject1\\olsmap.png")
    status['text'] = "Success!....,OLS complete! PNG and PDF maps exported and saved."    
    
    # Update the GUI with the new map image    
    image3 = ImageTk.PhotoImage(file="C:\\MyUW\\SummerProject1\\olsmap.png")
    widgetf.configure(image=image3)
    widgetf.image = image3
    Image.ANTIALIAS
       
    
# Create a function to view the IDW raster
def viewIDW():
    try:
        image2 = ImageTk.PhotoImage(file="C:\\MyUW\\SummerProject1\\idwmap.png")
        widgetf.configure(image=image2)
        widgetf.image = image2
    except:
        status['text'] = "Raster Not Found. Run the application again..."        

# Create a function to view the OLS raster
def viewOLS():
    try:
        image3 = ImageTk.PhotoImage(file="C:\\MyUW\\SummerProject1\\olsmap.png")
        widgetf.configure(image=image3)
        widgetf.image = image3
    except:
        status['text'] = "Error....File Not Found!.try again!..."     
        
# Create a function to view the project Files
def viewProjectFiles():
    try:
        filenames = tkFileDialog.askopenfilename(initialdir = "/", title = "Select file", filetypes = (("jpeg files", "*.jpg"), ("all files", "*.*")))
        print (root.filename)                                                                       
    except:
        status['text'] = "Error.....Files Not Found!. try again!.."        

# Create a function to view the project demo video
def viewprojectDemoVideo():
    try:
        os.system("C:\\MyUW\\SummerProject1\\project1_RoselineBatcha.mp4")
    except:
        status['text'] = "Error!..Demo Video Not Found. Try again!..."     
        
    
# Create a new label frame for the About section
about = Frame(root, highlightbackground="green", highlightcolor="green", highlightthickness=.5, bg="grey")
about.pack(padx=10, pady=10)

# Title for the about frame
aboutTitle = Text(about, width=8, height=1, borderwidth=0, bg="grey", highlightthickness=0, wrap=WORD)
aboutTitle.insert(INSERT, "ABOUT")
aboutTitle.config(state=DISABLED)
aboutTitle.configure(font=("Book Antiqua", 14))
aboutTitle.pack(pady=2)

# Text inside of the about frame
aboutLabl = Text(about, width=30, height=10, borderwidth=0, highlightthickness=0, wrap=WORD, bg="grey")
aboutLabl.insert(INSERT, "This application searches for a relationship between nitrate levels in drinking water and cancer occurrences for census tracts in the state of Wisconsin over a ten year period. IDW, Regression and statistics present a possible role of water nitrate levels in occurence cancer incidence.")
aboutLabl.config(state=DISABLED)
aboutLabl.configure(font=("Ariel", 11))
aboutLabl.pack(padx=1)

# Create a new label frame for the analysis section
run = Frame(root, highlightbackground="green", highlightcolor="green", highlightthickness=.5, bg="grey")
run.pack(padx=10, pady=10)

# Title for the analysis frame
runTitle = Text(run, width=12, height=1, borderwidth=0, bg="grey", highlightthickness=0, wrap=WORD)
runTitle.insert(INSERT, "Run Analysis")
runTitle.config(state=DISABLED)
runTitle.configure(font=("Book Antiqua", 12))
runTitle.pack(padx=4, pady=2)

# Text inside of the analysis frame
runLabl = Label(run, text="Please enter a power (k) value:", relief=RAISED, bg="white")
runLabl.pack()

# Create a text box for the k value input
k = Entry(run, bg="white")
k.pack(pady=1)

# Create a button to run the IDW, Zonal Statistics, and OLS
runB = Button(run, text ="Run", command=runIDW)
runB.pack(pady=1)

# Create a new label frame for the Results section
results = Frame(root, highlightbackground="green", highlightcolor="green", highlightthickness=.5, bg="grey")
results.pack(padx=10, pady=10)

# Title for the results frame
resTitle = Text(results, width=12, height=1, borderwidth=0, bg="grey", highlightthickness=0, wrap=WORD)
resTitle.insert(INSERT, "View Results")
resTitle.config(state=DISABLED)
resTitle.configure(font=("Book Antiqua", 12))
resTitle.pack(padx=4, pady=2)

# Text inside of the results frame
resLabl = Label(results, text="Select raster output to display:", bg="grey")
resLabl.pack()

# Create a button to show either the IDW raster or the OLS output
idwB = Button(results, text ="IDW", command=viewIDW)
idwB.pack(side="left", padx=10, pady=10)
regB = Button(results, text ="Regression", command=viewOLS)
regB.pack(side="right", padx=10, pady=10)

# Create a new label frame for the Project files and Demo Video section
files = Frame(root, highlightbackground="green", highlightcolor="green", highlightthickness=.5, bg="grey")
files.pack(padx=10, pady=10)

# Title for the results frame
filesTitle = Text(files, width=12, height=1, borderwidth=0, bg="grey", highlightthickness=0, wrap=WORD)
filesTitle.insert(INSERT, "View Files")
filesTitle.config(state=DISABLED)
filesTitle.configure(font=("Book Antiqua", 12))
filesTitle.pack(padx=4, pady=2)

# Text inside of the Project and Video frame
filesLabl = Label(files, text="Select Project Files and  Demo Video to display:", bg="grey")
filesLabl.pack()

# Create a button to show either the project files or the video output
pfB = Button(files, text ="Project Files", command=viewProjectFiles)
pfB.pack(side="left", padx=10, pady=10)
dvB = Button(files, text ="Project Demo", command=viewprojectDemoVideo)
dvB.pack(side="right", padx=10, pady=10)                                                                                                                                                                                                         
# Create a status bar
status = Label(root, text="Spatial analysis running...", borderwidth=1, relief=SUNKEN, anchor=W, bg="green")
status.pack(side=BOTTOM, fill=X)

root.mainloop()
