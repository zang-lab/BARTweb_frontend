# -*- coding: utf-8 -*-
from __future__ import division
import os, sys, time
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
def generate_user_key(user_email, jobname):
    '''
    generate key according to e-mail or jobname
    '''

    logger.info("Init project: generate key ...")
    tstamp = str(time.time()).replace('.','') # userkey: name_timestamp

    userkey_prefix = ""
    # if jobname is null    
    if jobname == '':
        if user_email == '': 
            logger.info("Init project: user does not input e-mail or jobname...")
            userkey_prefix = 'anonymous'
        else:
            logger.info("Init project: user e-mail is {}...".format(user_email))
            userkey_prefix = user_email.split('@')[0]
    # if jobname is not null, generate key according to jobname
    else: 
        logger.info("Init project: user jobname is {}...".format(jobname))
        userkey_prefix = jobname.replace(' ', '')  # get rid of spaces
    
    user_key = userkey_prefix + '_' + tstamp
    logger.info("Init project: user key is {}...".format(user_key))

    return user_key

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
    #utils.send_sqs_message(user_key)  # TODO: uncomment for online testing

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

    if user_data['dataType'] != 'HiC':
        bart_input = os.path.join(user_data['user_path'], 'upload/' + user_data['files'])
    else:
        bart_input = []
        bart_input.append(os.path.join(user_data['user_path'], 'upload/' + user_data['control_index_file']))
        bart_input.append(os.path.join(user_data['user_path'], 'upload/' + user_data['control_matrix_file']))
        bart_input.append(os.path.join(user_data['user_path'], 'upload/' + user_data['treatment_index_file']))
        bart_input.append(os.path.join(user_data['user_path'], 'upload/' + user_data['treatment_matrix_input']))
    bart_species = user_data['assembly']
    bart_output_dir = os.path.join(user_data['user_path'], 'download/')
    if user_data['dataType'] == 'Geneset':
        excutable = 'python3 bin/bart2 geneset -i '+bart_input+' -s '+bart_species+' --outdir '+bart_output_dir+' > {} 2>&1 '.format(os.path.join(user_data['user_path'],'log/mb_pipe.log'))+'\n'
    if user_data['dataType'] == 'ChIP-seq':
        ext = user_data['files'].split('.')[-1]
        if ext == 'bam':
            excutable = 'python3 bin/bart2 profile -f bam -i '+bart_input+' -s '+bart_species+' --outdir '+bart_output_dir+' > {} 2>&1 '.format(os.path.join(user_data['user_path'],'log/mb_pipe.log')) +'\n'
        elif ext == 'bed':
            excutable = 'python3 bin/bart2 profile -f bed -i '+bart_input+' -s '+bart_species+' --outdir '+bart_output_dir+' > {} 2>&1 '.format(os.path.join(user_data['user_path'],'log/mb_pipe.log')) +'\n'
        else:
            logger.error("illegal file extension")
    if user_data['dataType'] == 'regions':
        excutable = 'python3 bin/bart2 region -i '+bart_input+' -s '+bart_species+' --outdir '+bart_output_dir+' > {} 2>&1 '.format(os.path.join(user_data['user_path'],'log/mb_pipe.log'))+'\n'
    if user_data['dataType'] == 'HiC':
        excutable = 'python3 bin/bart2 diffHiC -ic '+bart_input[0]+' -mc '+bart_input[1]+' -it '+bart_input[2]+' -mt '+bart_input[3]+' -s '+bart_species+' --outdir '+bart_output_dir+' > {} 2>&1 '.format(os.path.join(user_data['user_path'],'log/mb_pipe.log'))+'\n'
    excute_send_email = 'python3 send_finish_email.py {}\n'.format(user_data['user_path'])
    excutable_file = os.path.join(user_data['user_path'], 'run_bart.sh')
    with open(excutable_file, 'w') as fopen:
        fopen.write(excutable)
        fopen.write(excute_send_email)
    fopen.close()


    '''
    write a shell for running bart


    #TODO: what Yifan should do.. run a shell script according to user.config data
    bart geneset -i project_dir/usercase/***/upload -s hg38/mm10 -o project_dir/usercase/***/download

    '''
    pass


# ===  show result part ===



# ====================================

# TODO: according to new file architecture which is
# - usercase/ 
#   - a_***/
#     - download/ ***

def generate_results(user_data):
    results = {}
    results['user_conf'] = {}
    results['user_conf']['Job_key'] = user_data['user_key']
    results['user_conf']['Species'] = user_data['assembly']
    results['user_conf']['Input_data_type'] = user_data['dataType']
    #this line is the file name in our own filesystem, does not need to show to user
    #results['user_conf']['Input_data'] = user_data['files']
    #this is the actrual file name that the user uploaded
    if user_data['dataType'] != 'HiC':
        results['user_conf']['Input_data'] = user_data['original_input']
    else:
        results['user_conf']['control_index_input'] = user_data['control_index_input']
        results['user_conf']['control_matrix_input'] = user_data['control_matrix_input']
        results['user_conf']['treatment_index_input'] = user_data['treatment_index_input']
        results['user_conf']['treatment_matrix_input'] = user_data['treatment_matrix_input']
    results['done'] = is_bart_done(user_data)
    if 'error' in user_data:
        results['error'] = user_data['error']
    if results['done']:
        bart_file_results, bart_table_results = generate_bart_file_results(user_data)
        results.update(bart_file_results)
        results.update(bart_table_results)
    else:
        results['proc_log'] = '/log/{}___{}'.format(user_data['user_key'],'mb_pipe.log')


    return results  




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
    files = os.listdir(bart_output_dir)
    count = 0
    if user_data['dataType'] == 'Geneset':
        for file in files:
            if utils.is_file_zero(os.path.join(bart_output_dir, file)):
                continue

            if '_auc.txt' in file: 
                count = count+1
            if '_bart_results.txt' in file: 
                count = count+1
            if '_adaptive_lasso_Info.txt' in file: 
                count = count+1
            if '_enhancer_prediction_lasso.txt' in file: 
                count = count+1
        if count==4:
            done = True
    if user_data['dataType'] == 'ChIP-seq' or user_data['dataType'] == 'regions' or user_data['dataType'] == 'HiC':
        for file in files:
            if utils.is_file_zero(os.path.join(bart_output_dir, file)):
                continue

            if '_auc.txt' in file: 
                count = count+1
            if '_bart_results.txt' in file: 
                count = count+1
        if count==2:
            done = True
    return done


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
