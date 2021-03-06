# !/usr/bin/python
# -*- coding=utf-8 -*-
# Python 2.7 script (bitshuffle uses python 2)
#    Copyright (C) 2015 by
#    Ranaivo Razakanirina <ranaivo.razakanirina@atety.com>
#    All rights reserved.
#    BSD license.

from __future__ import division
import time
import sys
import os.path
import numpy as np
import roohypy.tools as tl
import roohypy.models as md
import roohypy.tools.hdf5 as hd
import scipy.sparse as sparse

import gmpy2 as g2


def GetDefaultGTSimulationConfigs():
  """This function returns the default GT simulation configuration
  """
  # Simulation configurations
  simulation = {}
  simulation['epochs'] = 100
  simulation['alpha_mu_interval'] = 200
  simulation['resultfolder'] = './results/' # With trailing slash
  simulation['rand_ic'] = False
  simulation['alpha_mu_chunk_size'] = 16
  simulation['epochs_chunk_size'] = 100
  simulation['integer_sensitivity'] = 10000

  # If True, this parameter defines homogeneous initial condition or not.
  # Default is True with c0=300, g0=40, p0=10
  simulation['using_c0_g0'] = True
  simulation['c0'] = 300
  simulation['g0'] = 40
  simulation['p0'] = 10

  # If True, this parameter saves only in hdf5 file some chunk id
  # Default is False. If True, define saved_chunkids
  simulation['selectchunk'] = False
  #simulation['saved_chunkids'] = {1, 2}

  # Define the number of processors on multicore processor
  simulation['n_processors'] = 1
  
  return simulation


def InitGTSimulation(network,
        simulation={},
        attributes={}, simulation_index=0, icf=False, icfile=''):
    """This function inits all necessary temporary variables
    needed for a GT simulation.
    """
    # mp.dps = 50 # Set high decimal precision
    
    print(simulation)

    
    # Process network data
    nodefilepath = (network['networkfolder'] + 
        network['networkname']  + '/nodes.csv')
    edgefilepath = (network['networkfolder'] + 
        network['networkname']  + '/edges.csv')
    A = md.edgeNodeCsvToAdj(nodefilepath, edgefilepath)
    n, csc_A, elt_indices, \
        elt_indices_tr, attributes = md.getMainNetworkCharacteristics(A)
    attributes['networkname'] = network['networkname']
    
    # Get initial conditions from ic file and use icfile parameter
    # Otherwise, use rand_ic
    if icf:
        c_ic, g_ic, p_ic = tl.getICFromFile(icfile)
    else:
        # Process the initial conditions
        # and some attributes of the simulation
        if simulation['rand_ic']==True:
            c_ic, g_ic, p_ic = tl.getRandomUniformIC(
                c_tot=g2.mpfr(simulation['c_tot']),
                g_tot=g2.mpfr(simulation['g_tot']),
                alpha_mu_interval=simulation['alpha_mu_interval'],
                c_min_lim=simulation['c_min_lim'],
                g_min_lim=simulation['g_min_lim'],
                n=n
            )
        else:
            if simulation['using_c0_g0']==True:
                c_ic, g_ic, p_ic  = tl.getHomogeneousInitialConditions(
                    g2.mpfr(simulation['c0']),
                    g2.mpfr(simulation['g0']), 
                    g2.mpfr(simulation['p0']),
                    n)
            else:
                c_ic, g_ic, p_ic  = tl.getHomogeneousInitialConditions(
                    g2.mpfr(simulation['c_tot']) / g2.mpfr(n), 
                    g2.mpfr(simulation['g_tot']) / g2.mpfr(n), 
                    g2.mpfr(simulation['p0']),
                    n)
    
    # Get all possible combinations of values of alpha and mu
    # and build the chunks for epochs and alpha_mu
    alphas_mus, \
    alphas_mus_indices, \
    alpha_mu_to_index, \
    index_to_alpha_mu = md.getListOfAlphaMu(simulation['alpha_mu_interval'])
    n_combinations = len(alphas_mus)
    
    chunk_alpha_mu = tl.chunkList(alphas_mus_indices,
        simulation['alpha_mu_chunk_size'])
    chunk_am = tl.chunkList(alphas_mus, simulation['alpha_mu_chunk_size'])
    chunk_epoch = tl.chunkList(range(0, simulation['epochs'], 1),
            simulation['epochs_chunk_size'])
    
    epoch_min = list(map(lambda x: np.min(x), chunk_epoch))
    epoch_max = list(map(lambda x: np.max(x), chunk_epoch))
    tuple_t = zip(epoch_min, epoch_max)
    am_min = list(map(lambda x: np.min(x), chunk_alpha_mu))
    am_max = list(map(lambda x: np.max(x), chunk_alpha_mu))
    tuple_am = zip(am_min, am_max)

    # Create a dictionary to retrieve the id of 
    # a particular tuple_t (chunk_epoch_id)
    tuple_t_to_index = {}
    for index, value in enumerate(tuple_t):
        tuple_t_to_index[value] = index
    
    one = np.ones((n, simulation['alpha_mu_chunk_size'],
        simulation['epochs_chunk_size']), dtype=object)    
    cashini = one * c_ic.reshape((n, 1, 1))
    goodsini = one * g_ic.reshape((n, 1, 1))
    priceini = one * p_ic.reshape((n, 1, 1))
    
    cash = g2.mpfr('1') * np.zeros((n, simulation['alpha_mu_chunk_size'],
        simulation['epochs_chunk_size']+1), dtype=object)
    goods = g2.mpfr('1') * np.zeros((n, simulation['alpha_mu_chunk_size'],
        simulation['epochs_chunk_size']+1), dtype=object)
    price = g2.mpfr('1') * np.zeros((n, simulation['alpha_mu_chunk_size'],
        simulation['epochs_chunk_size']+1), dtype=object)
    
    # Build the temporary arrays and vectors for optimized GT-Model
    zeros, zeros1, \
    zeros_vector, zeros_vector1, \
    zeros_vector2, zeros_vector3 = md.getNullArraysAndVectors(n)
    
    # Create results folder and files
    resultname = tl.getResultFolderName(networkname=network['networkname'],
                step=simulation['alpha_mu_interval'],
                epochs=simulation['epochs'],
                integer_sensitivity=simulation['integer_sensitivity'])
    datasetfolder = simulation['resultfolder'] + resultname + '/'
    tl.checkCreateFolder(datasetfolder)
    datasetfullpath = (datasetfolder +
        'dataset_' + str(simulation_index) + '.h5')
    
    # Create hdf5 file
    f = hd.createGTHdf5File(datasetfullpath,
        shape=(n, n_combinations, simulation['epochs']),
        chunksize=(n, simulation['alpha_mu_chunk_size'],
        simulation['epochs_chunk_size']),
        epochs=simulation['epochs'],
        ordered_tuple_alpha_mu=alphas_mus,
        agents_id_list=range(0, n, 1),
        attributes=attributes,
        simulation=simulation,
        network=network,
        chunk_epoch=chunk_epoch
    )
    
    iterate = {}
    iterate['f'] = f
    iterate['tuple_am'] = tuple_am
    iterate['tuple_t'] = tuple_t
    iterate['tuple_t_to_index'] = tuple_t_to_index
    iterate['cashini'] = cashini
    iterate['goodsini'] = goodsini
    iterate['priceini'] = priceini
    iterate['index_to_alpha_mu'] = index_to_alpha_mu
    iterate['A'] = A
    iterate['csc_A'] = csc_A
    iterate['elt_indices'] = elt_indices
    iterate['elt_indices_tr'] = elt_indices_tr
    iterate['zeros'] = zeros
    iterate['zeros1'] = zeros1
    iterate['zeros_vector'] = zeros_vector
    iterate['zeros_vector1'] = zeros_vector1
    iterate['zeros_vector2'] = zeros_vector2
    iterate['zeros_vector3'] = zeros_vector3
    iterate['n'] = n

    return cash, goods, price, iterate


def LaunchGTSimulation(network,
        simulation={},
        attributes={}, simulation_index=0, icf=False, icfile=''):
    """This function launches a GT simulation.
    """
    
    # Default simulation values
    # If the simulation dict configuration is empty, use default configs
    if bool(simulation)==False:
      simulation = GetDefaultGTSimulationConfigs()
    
    # Init and launch the GT simulation
    cash, goods, price, iterate = InitGTSimulation(network,
                                        simulation=simulation,
                                        attributes=attributes,
                                        simulation_index=simulation_index,
                                        icf=icf, icfile=icfile)
    
    for pair_am in iterate['tuple_am']:
        cash[:,:,0] = iterate['cashini'][:,:,0]
        goods[:,:,0] = iterate['goodsini'][:,:,0]
        price[:,:,0] = iterate['priceini'][:,:,0]
        for pair_t in iterate['tuple_t']:
            print('Network ' + network['networkname'])
            print(pair_t)
            print(pair_am)
            start_time = time.time()

            # Compute each chunk
            cash, goods, price = md.optimizedGTModel6(
                pair_am, pair_t,
                iterate['index_to_alpha_mu'],
                iterate['A'], iterate['csc_A'], 
                iterate['elt_indices'], iterate['elt_indices_tr'],
                iterate['zeros'], iterate['zeros1'],
                iterate['zeros_vector'], iterate['zeros_vector1'],
                iterate['zeros_vector2'], iterate['zeros_vector3'],
                cash, goods, price,
                iterate['n'],
                n_processors=simulation['n_processors'])
            
            # Load in f
            iterate['f'] = hd.loadGTIterationToHdf5File(iterate['f'],
                pair_am, pair_t,
                cash, goods, price,
                integer_sensitivity=simulation['integer_sensitivity'],
                tuple_t_to_index=iterate['tuple_t_to_index'])
        
            # Take the last evolution and put it as initial condition 
            # of the next chunk
            cash[:,:,0] = cash[:,:,pair_t[1]-pair_t[0]+1]
            goods[:,:,0] = goods[:,:,pair_t[1]-pair_t[0]+1]
            price[:,:,0] = price[:,:,pair_t[1]-pair_t[0]+1]
        
            end_time = time.time()
            print(end_time - start_time)
            print('-----------')

    # Flush hdf5 memory to file
    iterate['f'].flush()
