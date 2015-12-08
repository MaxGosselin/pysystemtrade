"""
Get legacy data from .csv files

Used for quick examples / 'scaffolding'
"""

import os

import pandas as pd

from syscore.fileutils import get_pathname_for_package
from syscore.pdutils import pd_readcsv
from syscore.genutils import str_of_int

from sysdata.futuresdata import FuturesData

"""
Static variables to store location of data
"""
LEGACY_DATA_MODULE="sysdata"
LEGACY_DATA_DIR="legacycsv"

class csvFuturesData(FuturesData):
    """
        Get futures specific data from legacy csv files
        
        Extends the FuturesData class for a specific data source 
    
    """
    
    def __init__(self, datapath=None):
        """
        Create a FuturesData object for reading .csv files from datapath
        inherits from FuturesData

        We look for data in .csv files
        

        :param datapath: path to find .csv files (defaults to LEGACY_DATA_MODULE/LEGACY_DATA_DIR 
        :type datapath: None or str
        
        :returns: new csvFuturesData object
    
        >>> data=csvFuturesData()
        >>> data
        FuturesData object with 38 instruments
        
        """

        if datapath is None:            
            datapath=get_pathname_for_package(LEGACY_DATA_MODULE, [LEGACY_DATA_DIR])

        """
        Most Data objects that read data from a specific place have a 'source' of some kind
        Here it's a directory
        """
        setattr(self, "_datapath", datapath)
    
    
    def get_instrument_price(self, instrument_code):
        """
        Get instrument price
        
        :param instrument_code: instrument to get prices for 
        :type instrument_code: str
        
        :returns: pd.DataFrame

        >>> data=csvFuturesData(datapath="tests/")
        >>> data.get_instrument_price("EDOLLAR").tail(2)
                      price
        2015-04-21  97.9050
        2015-04-22  97.8325
        >>> data["US10"].tail(2)
                         price
        2015-04-21  129.390625
        2015-04-22  128.867188
        """
        
        ## Read from .csv
        filename=os.path.join(self._datapath, instrument_code+"_price.csv")
        instrpricedata=pd_readcsv(filename)
        instrpricedata.columns=["price"]
        
        return instrpricedata
    
    def get_instrument_raw_carry_data(self, instrument_code):
        """
        Returns a pd. dataframe with the 4 columns PRICE, CARRY, PRICE_CONTRACT, CARRY_CONTRACT
        
        These are specifically needed for futures trading
        
        :param instrument_code: instrument to get carry data for 
        :type instrument_code: str
        
        :returns: pd.DataFrame
    
        >>> data=csvFuturesData(datapath="tests/")
        >>> data.get_instrument_raw_carry_data("EDOLLAR").tail(5)
                     PRICE    CARRY CARRY_CONTRACT PRICE_CONTRACT
        2015-04-16  97.860  97.9350         201806         201809
        2015-04-17  97.865  97.9400         201806         201809
        2015-04-20  97.850  97.9250         201806         201809
        2015-04-21  97.830  97.9050         201806         201809
        2015-04-22     NaN  97.8325         201806         201809
        """

        filename=os.path.join(self._datapath, instrument_code+"_carrydata.csv")
        instrcarrydata=pd_readcsv(filename)
        instrcarrydata.columns=["PRICE", "CARRY", "CARRY_CONTRACT", "PRICE_CONTRACT"]

        instrcarrydata.CARRY_CONTRACT=instrcarrydata.CARRY_CONTRACT.apply(str_of_int)
        instrcarrydata.PRICE_CONTRACT=instrcarrydata.PRICE_CONTRACT.apply(str_of_int)
        
        return instrcarrydata

    def _get_instrument_data(self):
        """
        Get a data frame of interesting information about instruments, eithier from a file or cached
                
        :returns: pd.DataFrame

        >>> data=csvFuturesData(datapath="tests/")
        >>> data._get_instrument_data()
                   Instrument  Pointsize AssetClass Currency
        Instrument                                          
        EDOLLAR       EDOLLAR       2500       STIR      USD
        US10             US10       1000       Bond      USD
        """
        
        filename=os.path.join(self._datapath, "instrumentconfig.csv")
        instr_data=pd.read_csv(filename)
        instr_data.index=instr_data.Instrument

        return instr_data

    def get_instrument_list(self):
        """
        list of instruments in this data set
        
        :returns: list of str

        >>> data=csvFuturesData(datapath="tests/")
        >>> data.get_instrument_list()
        ['EDOLLAR', 'US10']
        >>> data.keys()
        ['EDOLLAR', 'US10']
        """

        instr_data=self._get_instrument_data()
        
        return list(instr_data.Instrument)

            

    def get_instrument_asset_classes(self):
        """
        Returns dataframe with index of instruments, column AssetClass

        >>> data=csvFuturesData(datapath="tests/")
        >>> data.get_instrument_asset_classes()
        Instrument
        EDOLLAR    STIR
        US10       Bond
        Name: AssetClass, dtype: object
        """ 
        instr_data=self._get_instrument_data()
        instr_assets=instr_data.AssetClass
            
        return instr_assets

    def get_value_of_block_price_move(self, instrument_code):
        """
        How much is a $1 move worth in value terms?
        
        :param instrument_code: instrument to get value for 
        :type instrument_code: str
        
        :returns: float

        >>> data=csvFuturesData(datapath="tests/")
        >>> data.get_value_of_block_price_move("EDOLLAR")
        2500
        """

        instr_data=self._get_instrument_data()
        block_move_value=instr_data.loc[instrument_code,'Pointsize']
        
        return block_move_value
        
    def get_instrument_currency(self, instrument_code):
        """
        What is the currency that this instrument is priced in?
        
        :param instrument_code: instrument to get value for 
        :type instrument_code: str
        
        :returns: str

        >>> data=csvFuturesData(datapath="tests/")
        >>> data.get_instrument_currency("US10")
        'USD'
        """

        instr_data=self._get_instrument_data()
        currency=instr_data.loc[instrument_code,'Currency']
        
        return currency
        
    def _get_fx_data(self, currency1, currency2):
        """
        Get fx data
        
        :param currency1: numerator currency 
        :type currency1: str

        :param currency2: denominator currency 
        :type currency2: str
        
        :returns: Tx1 pd.DataFrame, or None if not available

        >>> data=csvFuturesData()
        >>> # datapath="tests/"
        >>> data._get_fx_data("EUR", "USD").tail(2)
                     EURUSD
        2015-10-30  1.09774
        2015-11-02  1.09827
        >>> data._get_fx_cross("EUR", "GBP").tail(2)
                          fx
        2015-10-30  0.718219
        2015-11-02  0.714471
        """    

        if currency1==currency2:
            return self.get_default_series()

        
        filename=os.path.join(self._datapath, "%s%sfx.csv" % (currency1, currency2))
        try:
            fxdata=pd_readcsv(filename)
        except:
            return None
        
        fxdata.columns=["%s%s" % (currency1, currency2)]
        
        return fxdata
        
if __name__ == '__main__':
    import doctest
    doctest.testmod()