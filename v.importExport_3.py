#!/usr/bin/env python
#
#%Module
#%  description: Creates import/export commercial fluxes map starting from a .csv data file
#%  keywords: commercial fluxes
#%  keywords: import/export
#%End
#%option G_OPT_F_INPUT
#% key: fluxes
#% description: Input .csv file of fluxes data
#% required: yes
#%end
#%option G_OPT_V_INPUT
#% key: land
#% description: Input vector map of the studied zone
#% required: yes
#%end
#%option G_OPT_V_OUTPUT
#% key: lIm
#% description: Output line vector map of import fluxes
#% required: no
#%end
#%option G_OPT_V_OUTPUT
#% key: pIm
#% description: Output point vector map (arrows showing direction) of import fluxes
#% required: no
#%end
#%option G_OPT_V_OUTPUT
#% key: lEx
#% description: Output line vector map of export fluxes
#% required: no
#%end
#%option G_OPT_V_OUTPUT
#% key: pEx
#% description: Output point vector map (arrows showing direction) of export fluxes
#% required: no
#%end

import sys,os,re
import grass.script as grass

def main():
	if not os.environ.has_key("GISBASE"):
		print "You must be in GRASS GIS to run this program."
		sys.exit(1)
	
	fluxes = options['fluxes']
	land = options['land']
	out_importLines = options['lIm']
	out_pointImport = options['pIm']
	out_exportLines = options['lEx']
	out_pointExport = options['pEx']
	
	fileI=open(fluxes,'r')
	fileLines=fileI.readlines()
	
	grass.run_command('g.region',vect=land)
	grass.run_command('v.db.addcolumn',map=land,columns='import double precision,export double precision')
	landname=(fluxes.split('_')[1]).split('.')[0]
	grass.run_command('v.extract',input=land,type='centroid',output='pointNation',where="name='%s'" % (landname))
	grass.run_command('v.type',input='pointNation',from_type='centroid',to_type='point',output='pointNation1')
	grass.run_command('v.extract',flags='r',input=land,output='allNations',where="name='%s'" % (landname))
	grass.run_command('v.db.addcolumn',map='pointNation1',columns='distance double precision')
	grass.run_command('v.distance',flags='a',_from='pointNation1',from_type='point',to='allNations',to_type='centroid',output='exportLines',upload='dist',column='distance')
	grass.run_command('v.category',input='exportLines',option='add',output='exportLines1')
	grass.run_command('v.db.addtable',map='exportLines1',columns='name varchar(30),endE double precision,endN double precision,import double precision,export double precision,azimuth double precision')
	grass.run_command('v.to.db',map='exportLines1',type='line',option='end',columns='endE,endN')
	linesList=grass.read_command('db.select',flags='c',table='exportLines1').split('\n')
	for i in linesList[:-1]:
		east=i.split('|')[2]
		north=i.split('|')[3]
		attrList=grass.read_command('v.what',flags='ga',map='allNations',coordinates='%s,%s' % (east,north)).split('\n')
		for g in attrList:
			if re.match('name=',g):
				nameP=g.split('=')[1]
				grass.run_command('v.db.update',map='exportLines1',column='name',value=nameP,where='endE=%s' % (east))
		for h in fileLines:
			if re.match('import_'+nameP,h):
				importValue=float((h.split('=')[1]).split('\n')[0])
				grass.run_command('v.db.update',map='exportLines1',column='import',value=importValue,where='endE=%s' % (east))
			if re.match('export_'+nameP,h):
				exportValue=float((h.split('=')[1]).split('\n')[0])
				grass.run_command('v.db.update',map='exportLines1',column='export',value=exportValue,where='endE=%s' % (east))
	grass.run_command('g.copy',vect='exportLines1,importLines1')
	grass.run_command('v.edit',map='importLines1',ids='1-9999',tool='flip')
	grass.run_command('v.to.db',map='exportLines1',type='line',option='azimuth',columns='azimuth')
	grass.run_command('v.to.db',map='importLines1',type='line',option='azimuth',columns='azimuth')
	grass.run_command('v.to.points',input='exportLines1',output='pointExport',dmax='2000')
	grass.run_command('v.to.points',input='importLines1',output='pointImport',dmax='1400')
	grass.run_command('v.db.addcolumn',map='pointExport',columns='azimuth1 double precision')
	grass.run_command('v.db.update',map='pointExport',column='azimuth1',value='360-azimuth')
	grass.run_command('v.db.addcolumn',map='pointImport',columns='azimuth1 double precision')
	grass.run_command('v.db.update',map='pointImport',column='azimuth1',value='360-azimuth')
	grass.read_command('v.univar',flags='g',map='exportLines1',type='line',column='export')
	meanEx=float((grass.read_command('v.univar',flags='g',map='exportLines1',type='line',column='export').split('\n')[5]).split('=')[1])/2
	meanIm=float((grass.read_command('v.univar',flags='g',map='importLines1',type='line',column='import').split('\n')[5]).split('=')[1])/2
	grass.run_command('d.mon',start='wx1')
	grass.run_command('d.vect',map='allNations',type='boundary',color='232:158:20',fcolor='none')
	if meanIm > meanEx:
		grass.run_command('d.vect',map='importLines1',type='line',fcolor='191:191:191',color='191:191:191',width_column='import',width_scale='0.5')
		grass.run_command('d.vect',map='pointImport',type='point',color='191:191:191',fcolor='191:191:191',icon='basic/arrow3',size='1',size_column='import',rotation_column='azimuth1')
		grass.run_command('d.vect',map='exportLines1',type='line',fcolor='127:127:127',color='127:127:127',width_column='export',width_scale='0.5')
		grass.run_command('d.vect',map='pointExport',type='point',color='127:127:127',fcolor='127:127:127',icon='basic/arrow3',size='1',size_column='export',rotation_column='azimuth1')
	else:
		grass.run_command('d.vect',map='exportLines1',type='line',fcolor='127:127:127',color='127:127:127',width_column='export',width_scale='0.5')
		grass.run_command('d.vect',map='pointExport',type='point',color='127:127:127',fcolor='127:127:127',icon='basic/arrow3',size='1',size_column='export',rotation_column='azimuth1')
		grass.run_command('d.vect',map='importLines1',type='line',fcolor='191:191:191',color='191:191:191',width_column='import',width_scale='0.5')
		grass.run_command('d.vect',map='pointImport',type='point',color='191:191:191',fcolor='191:191:191',icon='basic/arrow3',size='1',size_column='import',rotation_column='azimuth1')
#	grass.run_command('g.copy',vect='importLines1,%s' % (out_importLines))
#	grass.run_command('g.copy',vect='pointImport,%s' % (out_pointImport))
#	grass.run_command('g.copy',vect='exportLines1,%s' % (out_exportLines))
#	grass.run_command('g.copy',vect='pointExport,%s' % (out_pointExport))

#TODO: cleaning procedure

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
