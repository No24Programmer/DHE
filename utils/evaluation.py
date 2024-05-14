import time
import logging

import torch
import numpy as np
from tqdm import tqdm


def batch_evaluation(batch_results, batch_data, gt_dict, ret_ranks, device):
    """
        Perform batch evaluation.
        """
    for i, result in enumerate(batch_results):
        target = batch_data[3][i]
        pos = batch_data[2][i]
        key = " ".join([
            str(batch_data[0][i][x].item()) for x in range(len(batch_data[0][i]))
            if x != pos
        ])

        # filtered setting
        rm_idx = torch.LongTensor(gt_dict[pos.item()][key]).to(device)
        rm_idx = torch.where(rm_idx != target, rm_idx, 0)
        result.index_fill_(0, rm_idx, -np.Inf)

        sortidx = torch.argsort(result, dim=-1, descending=True)

        if batch_data[4][i] == 1:
            ret_ranks['entity'] = torch.cat([ret_ranks['entity'], (torch.where(sortidx == target)[0] + 1)], dim=0)
        elif batch_data[4][i] == -1:
            ret_ranks['relation'] = torch.cat([ret_ranks['relation'], (torch.where(sortidx == target)[0] + 1)], dim=0)
        else:
            raise ValueError("Invalid `feature.mask_type`.")

        if torch.sum(batch_data[1][i]) == 3:
            if pos == 0:
                ret_ranks['2-r'] = torch.cat([ret_ranks['2-r'], (torch.where(sortidx == target)[0] + 1)], dim=0)
            elif pos == 1 or pos == 2:
                ret_ranks['2-ht'] = torch.cat([ret_ranks['2-ht'], (torch.where(sortidx == target)[0] + 1)], dim=0)
            else:
                raise ValueError("Invalid `feature.mask_position`.")
        elif torch.sum(batch_data[1][i]) > 3:
            if pos == 0:
                ret_ranks['n-r'] = torch.cat([ret_ranks['n-r'], (torch.where(sortidx == target)[0] + 1)], dim=0)
            elif pos == 1 or pos == 2:
                ret_ranks['n-ht'] = torch.cat([ret_ranks['n-ht'], (torch.where(sortidx == target)[0] + 1)], dim=0)
            elif pos > 2 and batch_data[4][i] == -1:
                ret_ranks['n-a'] = torch.cat([ret_ranks['n-a'], (torch.where(sortidx == target)[0] + 1)], dim=0)
            elif pos > 2 and batch_data[4][i] == 1:
                ret_ranks['n-v'] = torch.cat([ret_ranks['n-v'], (torch.where(sortidx == target)[0] + 1)], dim=0)
            else:
                raise ValueError("Invalid `feature.mask_position`.")
        else:
            raise ValueError("Invalid `feature.arity`.")
    return ret_ranks


def compute_metrics(ret_ranks):
    """
    Combine the ranks from batches into final metrics.
    """

    all_ent_ranks = ret_ranks['entity']
    all_rel_ranks = ret_ranks['relation']
    _2_r_ranks = ret_ranks['2-r']
    _2_ht_ranks = ret_ranks['2-ht']
    _n_r_ranks = ret_ranks['n-r']
    _n_ht_ranks = ret_ranks['n-ht']
    _n_a_ranks = ret_ranks['n-a']
    _n_v_ranks = ret_ranks['n-v']
    all_r_ranks = torch.cat([ret_ranks['2-r'], ret_ranks['n-r']], dim=0)
    all_ht_ranks = torch.cat([ret_ranks['2-ht'], ret_ranks['n-ht']], dim=0)

    mrr_ent = torch.mean(1.0 / all_ent_ranks).item()
    hits1_ent = torch.mean(torch.where(all_ent_ranks <= 1.0, 1.0, 0.0)).item()
    hits3_ent = torch.mean(torch.where(all_ent_ranks <= 3.0, 1.0, 0.0)).item()
    hits5_ent = torch.mean(torch.where(all_ent_ranks <= 5.0, 1.0, 0.0)).item()
    hits10_ent = torch.mean(torch.where(all_ent_ranks <= 10.0, 1.0, 0.0)).item()

    mrr_rel = torch.mean(1.0 / all_rel_ranks).item()
    hits1_rel = torch.mean(torch.where(all_rel_ranks <= 1.0, 1.0, 0.0)).item()
    hits3_rel = torch.mean(torch.where(all_rel_ranks <= 3.0, 1.0, 0.0)).item()
    hits5_rel = torch.mean(torch.where(all_rel_ranks <= 5.0, 1.0, 0.0)).item()
    hits10_rel = torch.mean(torch.where(all_rel_ranks <= 10.0, 1.0, 0.0)).item()

    mrr_2r = torch.mean(1.0 / _2_r_ranks).item()
    hits1_2r = torch.mean(torch.where(_2_r_ranks <= 1.0, 1.0, 0.0)).item()
    hits3_2r = torch.mean(torch.where(_2_r_ranks <= 3.0, 1.0, 0.0)).item()
    hits5_2r = torch.mean(torch.where(_2_r_ranks <= 5.0, 1.0, 0.0)).item()
    hits10_2r = torch.mean(torch.where(_2_r_ranks <= 10.0, 1.0, 0.0)).item()

    mrr_2ht = torch.mean(1.0 / _2_ht_ranks).item()
    hits1_2ht = torch.mean(torch.where(_2_ht_ranks <= 1.0, 1.0, 0.0)).item()
    hits3_2ht = torch.mean(torch.where(_2_ht_ranks <= 3.0, 1.0, 0.0)).item()
    hits5_2ht = torch.mean(torch.where(_2_ht_ranks <= 5.0, 1.0, 0.0)).item()
    hits10_2ht = torch.mean(torch.where(_2_ht_ranks <= 10.0, 1.0, 0.0)).item()

    mrr_nr = torch.mean(1.0 / _n_r_ranks).item()
    hits1_nr = torch.mean(torch.where(_n_r_ranks <= 1.0, 1.0, 0.0)).item()
    hits3_nr = torch.mean(torch.where(_n_r_ranks <= 3.0, 1.0, 0.0)).item()
    hits5_nr = torch.mean(torch.where(_n_r_ranks <= 5.0, 1.0, 0.0)).item()
    hits10_nr = torch.mean(torch.where(_n_r_ranks <= 10.0, 1.0, 0.0)).item()

    mrr_nht = torch.mean(1.0 / _n_ht_ranks).item()
    hits1_nht = torch.mean(torch.where(_n_ht_ranks <= 1.0, 1.0, 0.0)).item()
    hits3_nht = torch.mean(torch.where(_n_ht_ranks <= 3.0, 1.0, 0.0)).item()
    hits5_nht = torch.mean(torch.where(_n_ht_ranks <= 5.0, 1.0, 0.0)).item()
    hits10_nht = torch.mean(torch.where(_n_ht_ranks <= 10.0, 1.0, 0.0)).item()

    mrr_na = torch.mean(1.0 / _n_a_ranks).item()
    hits1_na = torch.mean(torch.where(_n_a_ranks <= 1.0, 1.0, 0.0)).item()
    hits3_na = torch.mean(torch.where(_n_a_ranks <= 3.0, 1.0, 0.0)).item()
    hits5_na = torch.mean(torch.where(_n_a_ranks <= 5.0, 1.0, 0.0)).item()
    hits10_na = torch.mean(torch.where(_n_a_ranks <= 10.0, 1.0, 0.0)).item()

    mrr_nv = torch.mean(1.0 / _n_v_ranks).item()
    hits1_nv = torch.mean(torch.where(_n_v_ranks <= 1.0, 1.0, 0.0)).item()
    hits3_nv = torch.mean(torch.where(_n_v_ranks <= 3.0, 1.0, 0.0)).item()
    hits5_nv = torch.mean(torch.where(_n_v_ranks <= 5.0, 1.0, 0.0)).item()
    hits10_nv = torch.mean(torch.where(_n_v_ranks <= 10.0, 1.0, 0.0)).item()

    mrr_r = torch.mean(1.0 / all_r_ranks).item()
    hits1_r = torch.mean(torch.where(all_r_ranks <= 1.0, 1.0, 0.0)).item()
    hits3_r = torch.mean(torch.where(all_r_ranks <= 3.0, 1.0, 0.0)).item()
    hits5_r = torch.mean(torch.where(all_r_ranks <= 5.0, 1.0, 0.0)).item()
    hits10_r = torch.mean(torch.where(all_r_ranks <= 10.0, 1.0, 0.0)).item()

    mrr_ht = torch.mean(1.0 / all_ht_ranks).item()
    hits1_ht = torch.mean(torch.where(all_ht_ranks <= 1.0, 1.0, 0.0)).item()
    hits3_ht = torch.mean(torch.where(all_ht_ranks <= 3.0, 1.0, 0.0)).item()
    hits5_ht = torch.mean(torch.where(all_ht_ranks <= 5.0, 1.0, 0.0)).item()
    hits10_ht = torch.mean(torch.where(all_ht_ranks <= 10.0, 1.0, 0.0)).item()

    eval_result = {
        'entity': {
            'mrr': mrr_ent,
            'hits1': hits1_ent,
            'hits3': hits3_ent,
            'hits5': hits5_ent,
            'hits10': hits10_ent
        },
        'relation': {
            'mrr': mrr_rel,
            'hits1': hits1_rel,
            'hits3': hits3_rel,
            'hits5': hits5_rel,
            'hits10': hits10_rel
        },
        'ht': {
            'mrr': mrr_ht,
            'hits1': hits1_ht,
            'hits3': hits3_ht,
            'hits5': hits5_ht,
            'hits10': hits10_ht
        },
        '2-ht': {
            'mrr': mrr_2ht,
            'hits1': hits1_2ht,
            'hits3': hits3_2ht,
            'hits5': hits5_2ht,
            'hits10': hits10_2ht
        },
        'n-ht': {
            'mrr': mrr_nht,
            'hits1': hits1_nht,
            'hits3': hits3_nht,
            'hits5': hits5_nht,
            'hits10': hits10_nht
        },
        'r': {
            'mrr': mrr_r,
            'hits1': hits1_r,
            'hits3': hits3_r,
            'hits5': hits5_r,
            'hits10': hits10_r
        },
        '2-r': {
            'mrr': mrr_2r,
            'hits1': hits1_2r,
            'hits3': hits3_2r,
            'hits5': hits5_2r,
            'hits10': hits10_2r
        },
        'n-r': {
            'mrr': mrr_nr,
            'hits1': hits1_nr,
            'hits3': hits3_nr,
            'hits5': hits5_nr,
            'hits10': hits10_nr
        },
        'n-a': {
            'mrr': mrr_na,
            'hits1': hits1_na,
            'hits3': hits3_na,
            'hits5': hits5_na,
            'hits10': hits10_na
        },
        'n-v': {
            'mrr': mrr_nv,
            'hits1': hits1_nv,
            'hits3': hits3_nv,
            'hits5': hits5_nv,
            'hits10': hits10_nv
        },
    }

    return eval_result


def predict(model, data_pyreader, all_facts, edge_labels, structure_bias_labels, device, logger, model_type):
    start = time.time()

    step = 0
    ret_ranks = dict()
    ret_ranks['entity'] = torch.empty(0).to(device)
    ret_ranks['relation'] = torch.empty(0).to(device)
    ret_ranks['2-r'] = torch.empty(0).to(device)
    ret_ranks['2-ht'] = torch.empty(0).to(device)
    ret_ranks['n-r'] = torch.empty(0).to(device)
    ret_ranks['n-ht'] = torch.empty(0).to(device)
    ret_ranks['n-a'] = torch.empty(0).to(device)
    ret_ranks['n-v'] = torch.empty(0).to(device)

    for i, data in tqdm(enumerate(data_pyreader), total=len(data_pyreader)):
        if model_type == "DHE":
            _, np_fc_out = model(data)
        else:
            _, np_fc_out = model.forward(data, edge_labels, structure_bias_labels)
        ret_ranks = batch_evaluation(np_fc_out, data, all_facts, ret_ranks, device)
        step += 1
    eval_performance = compute_metrics(ret_ranks)

    all_entity = "ENTITY\t\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f" % (
        eval_performance['entity']['mrr'],
        eval_performance['entity']['hits1'],
        eval_performance['entity']['hits3'],
        eval_performance['entity']['hits5'],
        eval_performance['entity']['hits10'])

    all_relation = "RELATION\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f" % (
        eval_performance['relation']['mrr'],
        eval_performance['relation']['hits1'],
        eval_performance['relation']['hits3'],
        eval_performance['relation']['hits5'],
        eval_performance['relation']['hits10'])

    all_ht = "HEAD/TAIL\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f" % (
        eval_performance['ht']['mrr'],
        eval_performance['ht']['hits1'],
        eval_performance['ht']['hits3'],
        eval_performance['ht']['hits5'],
        eval_performance['ht']['hits10'])

    all_r = "PRIMARY_R\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f" % (
        eval_performance['r']['mrr'],
        eval_performance['r']['hits1'],
        eval_performance['r']['hits3'],
        eval_performance['r']['hits5'],
        eval_performance['r']['hits10'])

    logger.info("\n-------- Evaluation Performance --------\n%s\n%s\n%s\n%s\n%s" % (
        "\t".join(["TASK\t", "MRR", "Hits@1", "Hits@3", "Hits@5", "Hits@10"]),
        all_ht, all_r, all_entity, all_relation))

    end = time.time()
    logger.info("Predict time: " + str(round(end - start, 3)) + 's')

    return eval_performance['entity']['mrr']

