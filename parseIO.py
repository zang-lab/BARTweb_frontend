# -*- coding: utf-8 -*-
from __future__ import division
import os, sys
import subprocess
import shutil
import json
import yaml
import numpy as np
import pandas as pd
import scipy
from scipy import special

import utils
from utils import model_logger as logger

PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))

# in html console.log(myResult)
# ===  process user input part ===
def generate_user_key(username, jobname):
    '''
    generate key according to e-mail or jobname
    '''

    logger.info("Init project: generate key ...")

    import time
    tstamp = time.time() # userkey: name_timestamp
    user_mail = username

    # if jobname is null    
    if jobname == '':
        if username == '': 
            logger.info("Init project: user does not input e-mail or jobname...")
            username = 'anonymous'
        else:
            logger.info("Init project: user e-mail is {}...".format(username))
            username = username.split('@')[0]
    # if jobname is not null, generate key according to jobname
    else: 
        logger.info("Init project: user jobname is {}...".format(jobname))
        username = jobname.replace(' ', '')  # get rid of spaces
    key = username + '_' + str(tstamp)

    logger.info("Init project: user key is {}...".format(key))

    # send key to user's e-mail	
    if username != "":	
        logger.info("Init project: send e-mail to {} for {}".format(user_mail, key))	
        send_flag, send_msg = utils.send_email(user_mail, key, 'Submit')	
        if send_flag:	
            logger.info("Init project: " + send_msg)	
        else:	
            logger.error("Init project:" + send_msg)
    else:
        logger.error("Init project: username is null")

    return key

def init_project_path(user_key):
    '''
    create project directories
    '''

    logger.info("Init project: init project path for {}...".format(user_key))

    user_path = os.path.join(PROJECT_DIR, 'usercase/' + user_key)
    user_upload_path = os.path.join(user_path, 'upload')
    user_download_path = os.path.join(user_path, 'download')
    user_log_path = os.path.join(user_path, 'log')

    utils.create_dir(user_path)
    utils.create_dir(user_upload_path)
    utils.create_dir(user_download_path)
    utils.create_dir(user_log_path)

    # create an empty log file 
    user_log_file_path = os.path.join(user_log_path, 'mb_pipe.log')	
    if not os.path.exists(user_log_file_path):	
        with open(user_log_file_path, 'w'): pass

    logger.info("Init project: send user key to Amazon SQS...")
    # utils.send_sqs_message(user_key)  # TODO: uncomment for online testing

    return user_path


def init_user_config(user_path, user_data):
    '''
    dump data into user.config
    '''

    logger.info("Save data: save data to user.config...")
    logger.info(user_data)

    # init username.config and save config data
    config_file = os.path.join(user_path, 'user.config')
    with open(config_file, 'w') as fopen:
        yaml.safe_dump(user_data, fopen, encoding='utf-8', allow_unicode=True, default_flow_style=False)


def get_user_data(user_key):
    '''
    load data from user.config

    '''

    logger.info("Get data: get data from user.config for {}...".format(user_key))

    user_path = os.path.join(PROJECT_DIR, 'usercase/' + user_key)
    config_file = os.path.join(user_path, 'user.config')

    # handle non-existing exception
    if not os.path.exists(config_file):
        return None

    with open(config_file, 'r') as fopen:
        user_data = yaml.load(fopen)

    return user_data


def is_user_key_exists(user_key):
    dest_path = os.path.join(PROJECT_DIR, 'usercase/' + user_key)
    return os.path.exists(dest_path)


def prepare_bart(user_data):

    bart_input = os.path.join(user_data['user_path'], 'upload/' + user_data['files'])
    bart_species = user_data['assembly']
    bart_output_dir = os.path.join(user_data['user_path'], 'download/')
    if user_data['dataType'] == 'Geneset':
        excutable = 'bart geneset -i '+bart_input+' -s '+bart_species+' --outdir '+bart_output_dir
    if user_data['dataType'] == 'ChIP-seq':
        excutable = 'bart profile -i '+bart_input+' -s '+bart_species+' --outdir '+bart_output_dir

    excutable_file = os.path.join(user_data['user_path'], 'run_bart.sh')
    with open(excutable_file, 'w') as fopen:
        fopen.write(excutable)
    fopen.close()
    '''
    write a shell for running bart


    #TODO: what Yifan should do.. run a shell script according to user.config data
    bart geneset -i project_dir/usercase/***/upload -s hg38/mm10 -o project_dir/usercase/***/download

    '''
    pass


# ===  show result part ===

def config_results(results, user_data):
    '''
    Copy user_data to results for demonstration page: user configuration

    results: related to template/result_demonstration.html
    user_data: user configuration
    '''
    results['user_conf'] = {}
    results['user_conf']['Job_key'] = user_data['user_key']
    results['user_conf']['Species'] = user_data['assembly']
    results['user_conf']['Input_data_type'] = user_data['dataType']
    results['user_conf']['Input_data'] = user_data['files']
    

# ====================================

# TODO: according to new file architecture which is
# - usercase/ 
#   - a_***/
#     - download/ ***

def generate_results(user_data):
    results = {}
    config_results(results, user_data)
    results['done'] = is_bart_done(user_data)

    if results['done']:
        bart_file_results, bart_table_results = generate_bart_file_results(user_data)
        results.update(bart_file_results)
        results.update(bart_table_results)


    return results  


def generate_marge_file_results(user_data, marge_data_path):
    '''
    If marge is done processing, generate marge results file for user to download.

    Input:   
    user_data: user configuration 

    Return:
    marge_file_results: related to marge file for downloading   
    '''
    # marge procedure log file path
    marge_file_results = {}
    marge_file_results['proc_log'] = []
    marge_file_results['marge_result_files'] = []

    if not user_data['marge']:
        return marge_file_results

    user_path = user_data['user_path']
    # marge output file path
    # marge_output_path = os.path.join(user_path, 'marge_data/margeoutput')

    marge_output_path = os.path.join(user_path, marge_data_path)
    marge_suffix_type = ['_enhancer_prediction.txt', '_all_relativeRP.txt', '_Strength.txt', '_all_RP.txt', '_target_regressionInfo.txt']
    for root, dirs, files in os.walk(marge_output_path):
        for file in files:
            for file_type in marge_suffix_type:
                if file_type in str(file):
                    # src_file = os.path.join(root, file)
                    # dest_file = os.path.join(user_path, 'download/' + file)
                    # shutil.copyfile(src_file, dest_file)
                    dest_file_url = '/download/%s___%s' % (user_data['user_key'], file)
                    marge_file_results['marge_result_files'].append((file, dest_file_url))

    return marge_file_results


def generate_bart_file_results(user_data):
    '''
    If bart is done processing, generate bart results file for user to download.

    Input:
    user_data: user configuration

    Return:
    bart_file_results: related to bart file for downloading
    # bart_chart_results: related to bart chart for demonstrating and downloading
    bart_table_results: related to bart table for demonstrating and downloading

    '''
    bart_file_results = {}
    # bart_chart_results = {}
    bart_table_results = {}

    bart_file_results['bart_result_files'] = []
    bart_table_results['bartResult'] = []
    # bart_chart_results['bart_chart_files'] = []

        # return bart_file_results, bart_chart_results, bart_table_results

    # bart output file path
    bart_output_dir = os.path.join(user_data['user_path'], 'download')
    for root, dirs, files in os.walk(bart_output_dir):
        for bart_file in files:
            if '_auc.txt' in bart_file:
                src_file = os.path.join(root, bart_file)
                dest_file_url = '/download/%s___%s' % (user_data['user_key'], bart_file)
                bart_file_results['bart_result_files'].append((bart_file, dest_file_url))
                
            if '_bart_results.txt' in bart_file:
                src_file = os.path.join(root, bart_file)
                dest_file_url = '/download/%s___%s' % (user_data['user_key'], bart_file)
                bart_file_results['bart_result_files'].append((bart_file, dest_file_url))
                # bart table results for demonstration
                bart_table_results['bartResult'] = parse_bart_results(src_file)

            if '_adaptive_lasso_Info.txt' in bart_file:
                src_file = os.path.join(root, bart_file)
                dest_file_url = '/download/%s___%s' % (user_data['user_key'], bart_file)
                bart_file_results['bart_result_files'].append((bart_file, dest_file_url))

            if '_enhancer_prediction_lasso.txt' in bart_file:
                src_file = os.path.join(root, bart_file)
                dest_file_url = '/download/%s___%s' % (user_data['user_key'], bart_file)
                bart_file_results['bart_result_files'].append((bart_file, dest_file_url))
                

                    # just finding chart files in bart_output/plot
                    # bart_chart_results['bart_chart_files'] = plot_top_tf(bart_df, bart_output_dir, AUCs)
        
    # return bart_file_results, bart_chart_results, bart_table_results
    return bart_file_results, bart_table_results


# for showing table
def parse_bart_results(bart_result_file):
    # tf_name, tf_score, p_value, z_score, max_auc, r_rank -> definition in result_demonstration.html
    
    bart_title = []
    bart_result = []
    with open(bart_result_file, 'r') as fopen:
        title_line = fopen.readline().strip()
        if 'irwin_hall_pvalue' in title_line: # add Irwi-Hall P-value
            bart_title = ['tf_name', 'tf_score', 'p_value', 'z_score', 'max_auc', 'r_rank', 'i_p_value']
        else:
            bart_title = ['tf_name', 'tf_score', 'p_value', 'z_score', 'max_auc', 'r_rank']

        line = fopen.readline().strip()
        while line:
            bart_result.append(dict(zip(bart_title, line.split('\t'))))
            line = fopen.readline().strip()
    return bart_result


# ===  bart related === 
# TODO:!!!!  whether bart is done under differnt mode geneset / ChIP-seq
# For geneset: 4 files
# For ChIP-seq: 2 files including _auc/_bart_result

def is_bart_done(user_data):
    done = False
    bart_output_dir = os.path.join(user_data['user_path'], 'download/')
    if user_data['dataType'] == 'Geneset':
        if len(os.listdir(bart_output_dir)) == 4:
            done = True
    if user_data['dataType'] == 'ChIP-seq':
        if len(os.listdir(bart_output_dir)) == 2:
            done = True
    return done
    


    # auc_flag = False
    # res_flag = False
    # result_dir = os.path.join(user_path, 'download/')
    # if not os.path.exists(result_dir):
    #     return False

    # for res_file in os.listdir(result_dir):
    #     if '_auc.txt' in res_file:
    #         auc_flag = True
    #     if '_bart_results.txt' in res_file:
    #         res_flag = True
    # return (auc_flag and res_flag)


# generate bart plot results
def generate_plot_results(bart_output_dir, tf_name):
    '''
    Generate the plot for each TF

    Input:
    bart_output_dir: bart result directory
    tf_name: TF name

    Return:
    plot_results: related to bart plot
    '''
    # _auc.txt and _bart_result.txt files
    bart_auc_ext = '_auc.txt'
    bart_res_ext = '_bart_results.txt'

    AUCs = {}
    tfs = {}
    bart_df = {}
    bart_title = []
    for root, dirs, files in os.walk(bart_output_dir):
        for bart_file in files:
            if bart_res_ext in bart_file:
                bart_result_file = os.path.join(root, bart_file)
                # parse the value with the title
                with open(bart_result_file, 'r') as fopen:
                    line = fopen.readline().strip()
                    if 'irwin_hall_pvalue' in line: # add Irwi-Hall P-value
                        bart_title = ['tf_name', 'tf_score', 'p_value', 'z_score', 'max_auc', 'r_rank', 'i_p_value']
                    else:
                        bart_title = ['tf_name', 'tf_score', 'p_value', 'z_score', 'max_auc', 'r_rank']
                bart_df = pd.read_csv(bart_result_file, sep='\t', names=bart_title[1:], index_col=0, skiprows=1)
            if bart_auc_ext in bart_file:
                bart_auc_file = os.path.join(root, bart_file)
                with open(bart_auc_file, 'r') as fopen:
                    for line in fopen:
                        tf_key, auc_equation = line.strip().split('\t')
                        auc = float(auc_equation.replace(' ', '').split('=')[1])
                        AUCs[tf_key] = auc

                for tf_key in AUCs.keys():
                    tf = tf_key.split('_')[0]
                    auc = AUCs[tf_key]
                    if tf not in tfs:
                        tfs[tf] = [auc]
                    else:
                        tfs[tf].append(auc)
    plot_results = {}
    plot_results['tf_name'] = tf_name

    # generate cumulative data
    cumulative_data = {}
    background = []
    for tf in tfs:
        background.extend(tfs[tf])
    target = tfs[tf_name]
    background = sorted(background)
    dx = 0.01
    x = np.arange(0,1,dx)
    by,ty = [],[]
    
    for xi in x:
        by.append(sum(i< xi for i in background )/len(background))
        ty.append(sum(i< xi for i in target )/len(target))

    cumulative_data['x'] = list(x)
    cumulative_data['bgY'] = by
    cumulative_data['tfY'] = ty
    cumulative_data = [dict(zip(cumulative_data,t)) for t in zip(*cumulative_data.values())]
    plot_results['cumulative_data'] = cumulative_data

    # rankdot data
    rankdot_data = []
    rankdot_pair = {}
    col = 'r_rank'
    for tf_id in bart_df.index:
        rankdot_pair['tf_name'] = tf_id
        rankdot_pair['rank_x'] = list(bart_df.index).index(tf_id)+1
        rankdot_pair['rank_y'] = -1*np.log10(irwin_hall_cdf(3*bart_df.loc[tf_id][col],3))
        rankdot_data.append(rankdot_pair)
        rankdot_pair = {}
    plot_results['rankdot_data'] = rankdot_data

    rankdot_pair['rank_x'] = list(bart_df.index).index(tf_name)+1
    rankdot_pair['rank_y'] = -1*np.log10(irwin_hall_cdf(3*bart_df.loc[tf_name][col],3))
    plot_results['rankdot_TF'] = [rankdot_pair]

    return plot_results

# Irwin-Hall Distribution for plot
def factorial(n):
    value = 1.0
    while n>1:
        value*=n
        n-=1
    return value

def logfac(n):
    if n<20:
        return np.log(factorial(n))
    else:
        return n*np.log(n)-n+(np.log(n*(1+4*n*(1+2*n)))/6.0)+(np.log(np.pi))/2.0

def irwin_hall_cdf(x,n):
    # pval = returned_value for down regulated
    # pval = 1 - returned_value for up regulated
    value,k = 0,0
    while k<=np.floor(x):
        value +=(-1)**k*(special.binom(n,k))*(x-k)**n
        k+=1
    return value/(np.exp(logfac(n)))


if __name__ == '__main__':
    parse_bart_results('/Users/marvin/Projects/flask_playground/usercase/a_1534972940.637962/download/genelist1_bart_results.txt')
