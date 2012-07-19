#   $Id: BciSignalProcessing.py 2898 2010-07-08 19:09:30Z jhill $
#   
#   This file is a BCPy2000 demo file, which illustrates the capabilities
#   of the BCPy2000 framework.
# 
#   Copyright (C) 2007-10  Jeremy Hill
#   
#   bcpy2000@bci2000.org
#   
#   This program is free software: you can redistribute it
#   and/or modify it under the terms of the GNU General Public License
#   as published by the Free Software Foundation, either version 3 of
#   the License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import numpy
from SigTools.Filtering import causalfilter
import copy
#################################################################
#################################################################

class BciSignalProcessing(BciGenericSignalProcessing):	
	
	#############################################################
	
	def Description(self):
		return "HP then abs() then LP signals (EMG processing)."
	
	#############################################################
	
	def Construct(self):
		parameters = [
			"PythonSig list ProcessChannels= 1 EDC % % % // List of channels to process",
			"PythonSig float HPCutoffHz= 10 10 0 % // HP filter cutoff frequency in Hz",
			"PythonSig int HPOrder= 8 8 0 % // HP filter order",
			"PythonSig float LPCutoffHz= 10 10 0 % // LP filter cutoff frequency in Hz",
			"PythonSig int LPOrder= 2 2 0 % // LP filter order",
		]
		states = [
			
		]
		return (parameters, states)
		
	#############################################################
	
	def Preflight(self, sigprops):
		#~ Called after Set Config is pressed.
		#~ Sanity check paramater values, verify the availability of state variables.
		#~ sigprops is a dict of SignalProperties.
		#~ Can return a dict of out_signal_props or (nOutputChannels, nOutputSamples)
		
		#sigprops also available in self.in_signal_props
		chn = self.inchannels()
		self.eegfs = self.nominal['SamplesPerSecond']
		
		#TODO: Check if there is a stimulus channel to pass through to the application
		
		# Check ProcessChannels
		pch = self.params['ProcessChannels'].val
		use_process = len(pch) != 0
		if use_process:
			if False in [isinstance(x, int) for x in pch]:
				nf = filter(lambda x: not str(x) in chn, pch)
				if len(nf): raise EndUserError, "ProcessChannels %s not in module's list of input channel names" % str(nf)
				self.procchan = [chn.index(str(x)) for x in pch]
			else:
				nf = [x for x in pch if x < 1 or x > len(chn) or x != round(x)]
				if len(nf): raise EndUserError, "Illegal ProcessChannels: %s" % str(nf)
				self.procchan = [x-1 for x in pch]
				
			#Check HPCutoffHz
			hpcutoff = self.params['HPCutoffHz'].val
			if hpcutoff*2 > self.eegfs: raise EndUserError, "HPCutoffHz must be less than %s" % str(self.eegfs / 2)
			
			#Add the raw_data output to the list of output channels.
			out_sig_props=copy.deepcopy(sigprops)
			chan_labels=out_sig_props['ChannelLabels'] #Since this is a shallow copy>>
			add_chan_labels=[]
			for cc in pch:
				add_chan_labels.append(cc+'_RAW')
			chan_labels.extend(add_chan_labels) #>> out_sig_props is automatically updated here.
			return out_sig_props
			
		#return (nOutputChannels, nOutputSamples)
		#set self.out_signal_props
		#or return sigprops (same type as sigprops input)
				
	#############################################################TMSTrigc TMSTriga NerveTrigc NerveTriga EDCc EDCa FCRc FCRa
	
	def Initialize(self, indim, outdim):
		#~ Called following Preflight. Pre-allocate objects here then attach them to self.
		pch = self.params['ProcessChannels'].val
		do_proc_chans = len(pch) != 0
		
		hpcutoff = self.params['HPCutoffHz'].val
		hporder  = self.params['HPOrder'].val
		if do_proc_chans and hporder and hpcutoff:
			self.hpfilter = causalfilter(type='highpass', order=hporder, freq_hz=hpcutoff, samplingfreq_hz=self.eegfs)
		else:
			self.hpfilter = None
			
		lpcutoff = self.params['LPCutoffHz'].val
		lporder  = self.params['LPOrder'].val	
		if do_proc_chans and lporder and lpcutoff:
			self.lpfilter = causalfilter(type='lowpass', order=lporder, freq_hz=lpcutoff, samplingfreq_hz=self.eegfs)
		else:
			self.lpfilter = None
		
	#############################################################
	
	def Process(self, sig):
		#~ Signal is available as a numpy.matrix in sig or as the instance attribute self.sig
		#~ We can return the processed signal here.
		if len(self.procchan):
			# Store a copy of the raw data from the channels to be processed.
			# These will be available to the Application module as '<channame>_RAW'
			# Or indexed at the end of the TransmitChannelList
			raw_data=sig[self.procchan,:]
			
			#HP Filter
			if self.hpfilter != None:
				sig[self.procchan,:] = self.hpfilter(sig[self.procchan,:], axis=1)
		
			#Rectify
			sig[self.procchan,:] = numpy.abs(sig[self.procchan,:])
		
			#LP Filter
			if self.lpfilter != None:
				sig[self.procchan,:] = self.lpfilter(sig[self.procchan,:], axis=1)
		#Concat the raw data to the bottom of the processed data
		#Should a scalar be returned instead of all the samples?
		return numpy.concatenate((sig,raw_data))
#################################################################
#################################################################