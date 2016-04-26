# -*- coding: utf-8 -*-
import ambry.bundle



class Bundle(ambry.bundle.Bundle):
    
    grain_map = {
        'pl':'place',
        'co':'county',
        'ca':'california',
        'cd':'subcounty',
        'ct':'tract',
        'zc': 'zcta',
        'na': None,
        're': 'region',
        'r4':'cmsa',
        'ms':'msa',
        'st':'california'
    }
    
    def init(self):
        
        pass
        #self.recode_map = { row.hci_race_eth_code:row.text_code for row in self.dep('race_eth_codes')}

    def edit_pipeline(self, pl):
        """Alter the pipeline to add the final routine and the custom partition selector"""
        
        from ambry.etl import SelectPartition
        
        # No longer needed, now that the table descriptions have been extracted
        #pl.final = [self.edit_descriptions]
        
        pl.select_partition = [SelectPartition(
        'dict(table=source.dest_table.name,'
        'segment=source.sequence_id,'
        'grain=bundle.grain_map.get(row.geotype.lower(),\'unk\'))'
        )]
        return pl
  
        
    def na_is_none(self, v):
        
        if v == 'NA' or v == '':
            return None
        else:
            return v
    
    def catch_dbz(self, row,  v):
        """On row 96767 of the Alameda Neighbohoor CHange file there is a
        very large value that looks like a divide-by-nearly-zero error"""

        try:
            if row.difference == 0:
                return None
        except KeyError:
            pass
            
        if v == 'NA':
            return None
        else:
            return v
        
    def version_date(self, v):
        """Deal with wacky version dates, like: 14APR13:10:31:45"""
        
        from dateutil import parser
        from xlrd.xldate import  xldate_as_datetime
        import ambry.valuetype
          
        try:
            v =  parser.parse("{}-{}-{}".format(v[0:2],v[2:5],v[5:7])).date()
        except:
            v = xldate_as_datetime(v, 0).date()
            
        return v
            
    def extract_geoid(self, v, row):
        
        from geoid.census import Place, County, State, Cosub, Tract, Zcta
        from geoid.civick import GVid
        import ambry.valuetype
        
        CA_STATE = 6
    
        
        if row.geotype == 'PL':
            r = Place(CA_STATE, int(row.geotypevalue)).convert(GVid)
        elif row.geotype == 'CO':
            gt = row.geotypevalue
            assert int(gt[0:2]) == CA_STATE
            r = County(CA_STATE, int(gt[2:])).convert(GVid)
        elif row.geotype == 'CA' or row.geotype == 'ST':
            r = State(CA_STATE).convert(GVid)
        elif row.geotype == 'CD':
            r = Cosub.parse(row.geotypevalue).convert(GVid)

        elif row.geotype == 'CT':
            try:
                r = Tract.parse(row.geotypevalue).convert(GVid)
            except ValueError:
                r = Tract.parse('06'+row.geotypevalue).convert(GVid)
        elif row.geotype == 'ZC':
            r = Zcta.parse(row.geotypevalue).convert(GVid)
        elif row.geotype == 'NA': # Sub-state region, not a census area
            r = None
        elif row.geotype == 'RE': # Sub-state region, not a census area
            r = None
        elif row.geotype == 'R4': # Sub-state region, not a census area
            r = None
        elif row.geotype == 'MS': # Probably an MSA or similar
            r = None
        else:
            self.error("Unknown geotype {} in row {}".format(row.geotype, row))
            r = None
    
        if r is None:
            return ambry.valuetype.FailedValue(None)
    
        return ambry.valuetype.Geoid(r)
        
    def extract_recode(self, row):
        """Extract and convert the race / ethnicity codes """
        
        try:
            return None #self.recode_map.get(row.race_eth_code, None)
        except KeyError:
            return None 
        
        
        
    def meta_add_gvid(self):
        """A meta phase routine to add the gvid columns to every table"""
        
        for t in self.tables:
            t.add_column('gvid',datatype='census.GVid', 
                description='GVid version of the geotype and geotypeval',
                transform='^extract_geoid')
                
        self.commit()
        
    def meta_add_recode(self):
        """A meta phase routine to add the race/eth code columns to every table"""
        
        for t in self.tables:
            t.add_column('reid',datatype='demo.RECode', 
                description='Civic Knowledge race / ethnicity code. ',
                transform='^extract_recode')
                
        self.build_source_files.schema.objects_to_record()
              
        self.commit()
    
        
        
    def extract_desc(self, v, row, accumulator):
        """Extract the table description from the ind_definition field"""
        
        # This is no longer needed. It was needed once, to extract the 
        # titles, but now that the titles are in the schema.csv, 
        # it doesn't need to be done again. 
        return
        
        # These value are mostly the same for every row, I think. 
        accumulator[row.ind_id] = row.ind_definition
        
        return v
        
    def edit_descriptions(self, pl):
        """Extract the values added to the accumulator by extract_desc and add 
        them to the table description"""
         
        # No longer needed. 
        return 
         
        from ambry.etl import CastColumns
        
        caster = pl[CastColumns]
        
        table = caster.source.dest_table
        
        table.description = ','.join( u'HCI Indicator {}: {}'.format(k, v) 
                     for k, v in caster.accumulator.items())

        self.commit()
        
    def meta_update_schema(self):
        
        
        def move(col_or_name, in_cols, out_cols):

            print '   ', col_or_name


            if isinstance(col_or_name, (str, unicode)):
                col = [c for c in in_cols if c.name == col_or_name][0]
            else:
                col = col_or_name
                
            in_cols.remove(col),
            out_cols.append(col)
            col.sequence_id = len(out_cols)+1000
            col.update_number(col)
         
            
        for t in self.tables:
            
            print '---- ', t.name
            
            in_cols = list(t.columns)
            reordered_columns = []
            
            move('id', in_cols, reordered_columns)
            
            for c in t.primary_dimensions:
                move(c, in_cols, reordered_columns)
                
                if c.label:
                    move(c.label, in_cols, reordered_columns)
                    
                for child in c.children:
                    move(child, in_cols, reordered_columns)
                    
                    if child.label:
                        move(child.label, in_cols, reordered_columns)
                    
                    
            for c in t.primary_measures:
               move(c, in_cols, reordered_columns)
               
               if c.label:
                   move(c.label, in_cols, reordered_columns)
                   
               for child in c.children:
                   move(child, in_cols, reordered_columns)
                   
                   if child.label:
                       move(child.label, in_cols, reordered_columns)
                   

            for c in reordered_columns:
                print c.sequence_id, c.vid, c.name, c.valuetype
                
           
            self.commit()
          
    
                   
        self.commit()
        self.build_source_files.schema.objects_to_record()
        self.commit()
        
                    
         
    def meta_print_schema(self):
    
    
        def move(col_or_name, tag):

            print '   ', tag, col_or_name

        
        for t in self.tables:
        
            if t.name != 'healthy_food':
                continue
        
            print '---- ', t.name
        
            in_cols = list(t.columns)
            reordered_columns = []
        
            move('id', 'i')
        
            for c in t.primary_dimensions:
                move(c, 'd')
            
                if c.label:
                    move(c.label, 'l')
                
                for child in c.children:
                    move(child, '+')
                    
                    if child.label:
                        move(child.label, 'l')
                    
                
            for c in t.primary_measures:
               move(c, 'm')
           
               if c.label:
                   move(c.label, 'l')
               
               for child in c.children:
                   move(child, "+")
                   
                   if child.label:
                       move(child.label, 'l')


    def print_row(self, v, row):
        print v, type(v), v.exc 
        return v

        
    def set_labels(self):
        from operator import itemgetter
        
        p = self.partition('cdph.ca.gov-hci-unemployment-county')

        for c in p.measuredim.primary_dimensions:
            print c.name, c.pstats.nuniques, c.label, c.labels
            
        df =  p.measuredim.md_frame(
                    unstack = False,
                    measure='unemployment_rate', 
                    p_dim='gvid', 
                    s_dim='raceth',
                    filtered_dims={ 'reportyear': '2006/2010'})
                              
                              
        df.to_csv('unemployment.csv')
      
 
            
        
        
        
        
        
        
        
                     
                     