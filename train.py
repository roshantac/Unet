import argparse
import logging
import os
import sys

import numpy as np
import torch
import torch.nn as nn
from torch import optim
from tqdm import tqdm
from kornia.losses import SSIM
from eval import eval_net
from unet import UNet
import datetime
from torch.utils.tensorboard import SummaryWriter
from utils.dataset import BasicDataset
from torch.utils.data import DataLoader, random_split


def test_net(net, device, test_loader):
    net.eval()
    test_loss = 0
    correct = 0
    start = datetime.datetime.now()
    with torch.no_grad():
        for data in test_loader:
            data['bg'] = data['bg'].to(device, dtype = torch.float32)
            data['fgbg'] = data['fgbg'].to(device, dtype = torch.float32)
            data['mask'] = data['mask'].to(device, dtype = torch.float32)
            data['depth'] = data['depth'].to(device, dtype = torch.float32) 
            output = net(data)
            loss1 = criterion(output[1], data['mask'])
            loss2 = criterion(output[0], data['depth']) 
            loss = loss1 + loss2 
            test_loss += loss
        print("Test loss :",test_loss/len(test_loader.dataset))
        print(" Time taken for test ", datetime.datetime.now()- start)
        print("ground truth")
        show(data['depth'].detach().cpu(),nrow=8)
        print("Depth")
        show(output[0].detach().cpu(),nrow=8) # depth
        print("mask")
        show(output[1].detach().cpu(),nrow=8) #mask
        
            
def train_net(net, device,train_loader, optimizer,scheduler, criterion ):
    init = datetime.datetime.now()
    net.train()    
    pbar = tqdm(train_loader)
    epoch_loss = 0  
    start =  datetime.datetime.now()
    for i,batch in enumerate(pbar):
        batch['bg'] = batch['bg'].to(device, dtype = torch.float32)
        batch['fgbg'] = batch['fgbg'].to(device, dtype = torch.float32)
        batch['mask'] = batch['mask'].to(device, dtype = torch.float32)
        batch['depth'] = batch['depth'].to(device, dtype = torch.float32) 
        #depth_pred, masks_pred
        output = net(batch)
        loss1 = criterion(output[1], batch['mask'])
        loss2 = criterion(output[0], batch['depth']) 
        loss = 2*loss1 + loss2 
        epoch_loss += loss.item()
        pbar.set_postfix(desc  = f' Loss : {loss.item()}  Loss(mask): {loss1.item()} Loss(depth): {loss2.item()}')
        optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_value_(net.parameters(), 0.1)
        optimizer.step()
        
    
    end=  datetime.datetime.now()
    print("Time taken for Training 1 epoch is: ", end-start)

#         print("ground truth")
#         show(batch['depth'].detach().cpu(),nrow=8)
#         print("Depth")
#         show(output[0].detach().cpu(),nrow=8) # depth
#         print("mask")
#         show(output[1].detach().cpu(),nrow=8) #mask
