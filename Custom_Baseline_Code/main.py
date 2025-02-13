import myaugmentations as my_aug
import myconfig
import mydataset
import mymodel
import myloss
import myoptimizer
import mytrain

import torch
import wandb
import numpy as np
import argparse

from datetime import datetime, timedelta
import random

from importlib import import_module

def seed_setting(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)  # if use multi-GPU
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    np.random.seed(seed)
    random.seed(seed)

Index = [0]
def main(config=None):
    Index[0] += 1
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Initialize a new wandb run
    with wandb.init() as run:
        now = datetime.now() + timedelta(hours=9)
        now = now.strftime("%Y-%m-%d_%H:%M:%S")
        run.name = run.config.name + f"_{Index[0]}"
        hparams = run.config

        # dataset
        dataset_module = getattr(import_module("mydataset"), hparams.dataset)

        transform_module = getattr(import_module("myaugmentations"), "get_transform")
        train_transform = transform_module(transform_name=hparams.train_transform)
        val_transform = transform_module(transform_name=hparams.val_transform)
        test_transform = transform_module(transform_name=hparams.test_transform)

        # train dataset
        train_dataset = dataset_module(data_dir=hparams.train_path, mode='train', transform=train_transform,
                                        dataset_path=hparams.dataset_path, category_names=hparams.category_names)
        # validation dataset
        val_dataset = dataset_module(data_dir=hparams.val_path, mode='val', transform=val_transform,
                                        dataset_path=hparams.dataset_path, category_names=hparams.category_names)
        # test dataset
        test_dataset = dataset_module(data_dir=hparams.test_path, mode='test', transform=test_transform,
                                        dataset_path=hparams.dataset_path, category_names=hparams.category_names)
        
        # DataLoader
        train_loader = torch.utils.data.DataLoader(dataset=train_dataset, batch_size=hparams.batch_size, shuffle=True, num_workers=4, collate_fn=mydataset.collate_fn)
        val_loader = torch.utils.data.DataLoader(dataset=val_dataset, batch_size=hparams.batch_size, shuffle=False, num_workers=4, collate_fn=mydataset.collate_fn)
        test_loader = torch.utils.data.DataLoader(dataset=test_dataset, batch_size=hparams.batch_size, num_workers=4, collate_fn=mydataset.collate_fn)

        # model
        model_module = getattr(import_module("mymodel"), "config_model")  # default: BaseModel
        model = model_module(model_name=hparams.model, num_classes=len(hparams.category_names)).to(device)
        model = torch.nn.DataParallel(model)

        # Loss function 정의
        criterion_module = getattr(import_module("myloss"), "get_criterion")  # default: BaseModel
        criterion = criterion_module(hparams.criterion)

        # Optimizer 정의
        optimizer_module = getattr(import_module("myoptimizer"), "get_optimizer")  # default: BaseModel
        optimizer = optimizer_module(model, optimizer_name=hparams.optimizer, lr=hparams.lr)
        # optimizer = torch.optim.Adam(params = model.parameters(), lr = learning_rate, weight_decay=1e-6)

        # Scheduler 정의
        scheduler_module = getattr(import_module("myoptimizer"), "get_scheduler")  # default: BaseModel
        scheduler = scheduler_module(hparams.scheduler, optimizer, hparams.lr_decay_step, 0.5)

        # try:
        mytrain.train(hparams.num_epochs, model, train_loader, val_loader, criterion, optimizer, scheduler, hparams.saved_dir, hparams.val_every,
                    device, category_names=hparams.category_names, saved_modelname=hparams.model)
        # except:
        #     print("*" * 20)
        #     print(f"Training Error - {run.name}")
        #     print("*" * 20)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=21, help='random seed (default: 21)')
    parser.add_argument('--batch_size', type=int, default=16, help='input batch size for training (default: 16)')
    parser.add_argument('--lr', type=float, default=1e-4, help='learning rate (default: 1e-4)')
    parser.add_argument('--epochs', type=int, default=1, help='number of epochs to train (default: 1)')
    args = parser.parse_args()

    myconfig.my_config['name'] = myconfig.my_config['name'] + "_" + datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

    wandb.login()
    sweep_id = wandb.sweep(myconfig.my_config, project="semantic_segmentation")
    wandb.agent(sweep_id, function=main, count=1)

    # train(args)