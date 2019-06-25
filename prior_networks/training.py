import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

from prior_networks.util_pytorch import calc_accuracy_torch

from typing import Dict, Any
import numpy as np


import time

class Trainer:
    def __init__(self, model, criterion,
                 train_dataset, test_dataset,
                 optimizer,
                 scheduler=None,
                 optimizer_params: Dict[str, Any] = None,
                 scheduler_params: Dict[str, Any] = None,
                 batch_size=50,
                 device=None,
                 log_interval: int = 100,
                 test_criterion=None):
        assert isinstance(model, nn.Module)
        assert isinstance(train_dataset, Dataset)
        assert isinstance(test_dataset, Dataset)

        self.model = model
        self.criterion = criterion
        self.device = device
        self.log_interval = log_interval
        if test_criterion is not None:
            self.test_criterion = test_criterion
        else:
            self.test_criterion = nn.CrossEntropyLoss()

        # Instantiate the optimizer
        if optimizer_params is None:
            optimizer_params = {}
        self.optimizer = optimizer(self.model.parameters(), **optimizer_params)

        # Instantiate the scheduler
        if scheduler_params is None:
            scheduler_params = {}
        self.scheduler = scheduler(self.optimizer, **scheduler_params)

        self.trainloader = DataLoader(train_dataset, batch_size=batch_size,
                                      shuffle=True, num_workers=1)
        self.testloader = DataLoader(test_dataset, batch_size=batch_size,
                                     shuffle=False, num_workers=1)

        # Lists for storing training metrics
        self.train_loss, self.train_accuracy, self.train_eval_steps = [], [], []
        # Lists for storing test metrics
        self.test_loss, self.test_accuracy, self.test_eval_steps = [], [], []

        self.steps: int = 0

    def train(self, n_epochs=None, n_iter=None, device=None):
        # Calc num of epochs
        if n_epochs is None:
            assert isinstance(n_iter, int)
            n_epochs = math.ceil(n_iter / len(self.trainloader))
        else:
            assert isinstance(n_epochs, int)

        for epoch in range(n_epochs):
            print(f'Training epoch: {epoch + 1} / {n_epochs}')
            # Train
            self.scheduler.step()
            start = time.time()
            self._train_single_epoch()

            # Test
            self.test(time=time.time()-start)
        return

    def _train_single_epoch(self):

        # Set model in train mode
        self.model.train()

        for i, data in enumerate(self.trainloader, 0):
            # Get inputs
            inputs, labels = data
            if self.device is not None:
                # Move data to adequate device
                inputs, labels = map(lambda x: x.to(self.device), (inputs, labels))

            # zero the parameter gradients
            self.optimizer.zero_grad()

            outputs = self.model(inputs)
            loss = self.criterion(outputs, labels)
            loss.backward()
            self.optimizer.step()

            # Update the number of steps
            self.steps += 1

            # log statistics
            if self.steps % self.log_interval == 0:
                probs = F.softmax(outputs, dim=1)
                self.train_accuracy.append(
                    calc_accuracy_torch(probs, labels, self.device).item())
                self.train_loss.append(loss.item())
                self.train_eval_steps.append(self.steps)

        return

    def test(self, time):
        """
        Single evaluation on the entire provided test dataset.
        Return accuracy, mean test loss, and an array of predicted probabilities
        """
        test_loss = 0.
        n_correct = 0  # Track the number of correct classifications

        # Set model in eval mode
        self.model.eval()
        with torch.no_grad():
            for i, data in enumerate(self.testloader, 0):
                # Get inputs
                inputs, labels = data
                if self.device is not None:
                    inputs, labels = map(lambda x: x.to(self.device),
                                         (inputs, labels))
                outputs = self.model(inputs)
                test_loss += self.test_criterion(outputs, labels).item()
                probs = F.softmax(outputs, dim=1)
                n_correct += torch.sum(torch.argmax(probs, dim=1) == labels).item()

        test_loss = test_loss / len(self.testloader)
        accuracy = n_correct / len(self.testloader.dataset)

        print(f"Test Loss: {np.round(test_loss, 3)}; Test Accuracy: {np.round(100.0*accuracy, 1)}%; Time Per Epoch: {np.round(time/60.0,1)} min")

        # Log statistics
        self.test_loss.append(test_loss)
        self.test_accuracy.append(accuracy)
        self.test_eval_steps.append(self.steps)
        return

# class AdamM(torch.optim.Adam):
#     def __init__(self,  params, lr=1e-3, momentum=0.9, beta2= 0.999, eps=1e-8,
#                  weight_decay=0, amsgrad=False):
#         defaults=dict(lr=lr, betas=(momentum, beta2), eps=eps, weight_decay=weight_decay, amsgrad=amsgrad)
#         super(AdamM, self).__init__(params, defaults)

# # todo: put the training into a class to reduce the functional programming clutter
# def test(model, testloader, batch_size=50, print_progress=True, device=None):
#     """
#     Single evaluation on the entire provided test dataset.
#     Return accuracy, mean test loss, and an array of predicted probabilities
#     """
#     criterion = nn.CrossEntropyLoss()
#
#     test_loss = 0.
#     n_correct = 0  # Track the number of correct classifications
#
#     model.eval()
#     with torch.no_grad():
#         for i, data in enumerate(testloader, 0):
#             # Get inputs
#             inputs, labels = data
#             if device is not None:
#                 inputs, labels = map(lambda x: x.to(device), (inputs, labels))
#             outputs = model(inputs)
#             test_loss += criterion(outputs, labels).item()
#             probs = F.softmax(outputs, dim=1)
#             n_correct += torch.sum(torch.argmax(probs, dim=1) == labels).item()
#     test_loss = test_loss / len(testloader)
#     accuracy = n_correct / len(testloader.dataset)
#
#     if print_progress:
#         print(f"Test Loss: {test_loss}; Test Accuracy: {accuracy}")
#     return accuracy, test_loss
#
# def train_single_epoch_with_ood(model, trainloader, oodloader, id_criterion, ood_criterion, gamma, optimizer, print_progress=True, device=None):
#     train_loss, train_accuracy = [], []
#
#     model.train()
#     running_loss = 0.0
#     for i, (data, ood_data) in enumerate(zip(trainloader, oodloader), 0):
#         # Get inputs
#         inputs, labels = data
#         ood_inputs, _ = ood_data
#         if device is not None:
#             inputs, labels, ood_inputs = map(lambda x: x.to(device), (inputs, labels, ood_inputs))
#
#
#         # zero the parameter gradients
#         optimizer.zero_grad()
#
#         id_outputs = model(inputs)
#         if gamma > 0.0:
#             inputs = torch.cat((inputs, ood_inputs), dim=0)
#             outputs = model(inputs)
#             id_outputs, ood_outputs = torch.chunk(outputs, 2, dim=0)
#             loss = id_criterion(id_outputs, labels) + gamma* ood_criterion(ood_outputs, None)
#         else:
#             loss = id_criterion(id_outputs, labels)
#         loss.backward()
#         optimizer.step()
#
#         # log statistics
#         train_loss.append(loss.item())
#         probs = F.softmax(id_outputs, dim=1)
#         train_accuracy.append(calc_accuracy_torch(probs, labels, device).item())
#
#         # print statistics
#         running_loss += loss.item()
#         if (i + 1) % 10 == 0:
#             if print_progress:
#                 print(f'[Step: {i + 1}] loss: {running_loss / 10.0}')
#             running_loss = 0.0
#     return train_loss, train_accuracy
#
#
# def train_procedure_with_ood(model, train_dataset, ood_dataset, test_dataset, n_epochs=80, lr=0.001, lr_decay=0.9,
#                              batch_size=50,
#                              match_dataset_length=False,
#                              id_criterion=None,
#                              ood_criterion=None,
#                              gamma=1.0,
#                              weight_decay=1e-8,
#                              print_progress='test',
#                              device=None):
#     print_train, print_test = _get_print_progress_vars(print_progress)
#
#     if id_criterion is None:
#         id_criterion = DirichletPriorNetLoss(target_concentration=100.0)
#     if ood_criterion is None:
#         ood_criterion = DirichletPriorNetLoss(target_concentration=0.0)
#     optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
#     scheduler = torch.optim.lr_scheduler.ExponentialLR(optimizer, lr_decay, last_epoch=-1)
#     if match_dataset_length:
#         # todo: Add functionality if OOD and regular datasets not the same lengths
#         # ood_dataset = adjust_dataset_length
#         pass
#     assert len(train_dataset) == len(ood_dataset)
#     trainloader = DataLoader(train_dataset, batch_size=batch_size,
#                              shuffle=True, num_workers=1, drop_last=True)
#     oodloader = DataLoader(ood_dataset, batch_size=batch_size,
#                            shuffle=True, num_workers=1, drop_last=True)
#     testloader = DataLoader(test_dataset, batch_size=batch_size,
#                             shuffle=False, num_workers=1)
#
#     # Lists for storing training metrics
#     train_loss, train_accuracy = [], []
#     # Lists for storing test metrics
#     test_loss, test_accuracy, test_steps = [], [], []
#
#     for epoch in range(n_epochs):
#         if print_progress:
#             print(f"Epoch: {epoch}")
#         # Train
#         scheduler.step()
#         epoch_train_loss, epoch_train_accuracy = train_single_epoch_with_ood(model, trainloader, oodloader,
#                                                                              id_criterion, ood_criterion, gamma, optimizer,
#                                                                              print_progress=print_train,
#                                                                              device=device)
#         train_loss += epoch_train_loss
#         train_accuracy += epoch_train_accuracy
#         # Test
#         accuracy, loss = test(model, testloader, print_progress=print_test, device=device)
#         test_loss.append(loss)
#         test_accuracy.append(accuracy)
#         test_steps.append(len(train_loss))
#     return train_loss, train_accuracy, test_loss, test_accuracy, test_steps


# def _get_print_progress_vars(print_progress):
#     """Helper function for setting the right print variables"""
#     if print_progress == 'all':
#         print_train = True
#         print_test = True
#     elif print_progress == 'test':
#         print_train = False
#         print_test = True
#     else:
#         print_train = False
#         print_test = False
#     return print_train, print_test

    # # class Training(object):
    # def train_single_epoch(model, trainloader, criterion, optimizer, print_progress=True, device=None):
    #     train_loss, train_accuracy = [], []
    #
    #     model.train()
    #     running_loss = 0.0
    #     for i, data in enumerate(trainloader, 0):
    #         # Get inputs
    #         inputs, labels = data
    #         if device is not None:
    #             # Move data to adequate device
    #             inputs, labels = map(lambda x: x.to(device), (inputs, labels))
    #
    #         # zero the parameter gradients
    #         optimizer.zero_grad()
    #
    #         outputs = model(inputs)
    #         loss = criterion(outputs, labels)
    #         loss.backward()
    #         optimizer.step()
    #
    #         # log statistics
    #         train_loss.append(loss.item())
    #         probs = F.softmax(outputs, dim=1)
    #         train_accuracy.append(calc_accuracy_torch(probs, labels, device).item())
    #
    #         # print statistics
    #         running_loss += loss.item()
    #         if (i + 1) % 10 == 0:
    #             if print_progress:
    #                 print(f'[Step: {i + 1}] loss: {running_loss / 10.0}')
    #             running_loss = 0.0
    #     return train_loss, train_accuracy
    #
    # def train_procedure(model, train_dataset, test_dataset, n_epochs=None, n_iter=None, lr=0.001, lr_decay=0.9,
    #                     batch_size=50,
    #                     loss=nn.CrossEntropyLoss,
    #                     print_progress='all',
    #                     device=None):
    #
    #     # Get bool variables for what to print during training
    #     print_train, print_test = _get_print_progress_vars(print_progress)
    #
    #     criterion = loss()
    #     optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-6)
    #     scheduler = torch.optim.lr_scheduler.ExponentialLR(optimizer, lr_decay, last_epoch=-1)
    #     trainloader = DataLoader(train_dataset, batch_size=batch_size,
    #                              shuffle=True, num_workers=1)
    #     testloader = DataLoader(test_dataset, batch_size=batch_size,
    #                             shuffle=False, num_workers=1)
    #
    #     # Lists for storing training metrics
    #     train_loss, train_accuracy = [], []
    #     # Lists for storing test metrics
    #     test_loss, test_accuracy, test_steps = [], [], []
    #
    #     # Calc num of epochs
    #     if n_epochs is None:
    #         n_epochs = math.ceil(n_iter / len(trainloader))
    #
    #     for epoch in range(n_epochs):
    #         if print_progress:
    #             print(f"Epoch: {epoch}")
    #         # Train
    #         scheduler.step()
    #         epoch_train_loss, epoch_train_accuracy = train_single_epoch(model, trainloader, criterion, optimizer,
    #                                                                     print_progress=print_train, device=device)
    #         train_loss += epoch_train_loss
    #         train_accuracy += epoch_train_accuracy
    #         # Test
    #         accuracy, loss = test(model, testloader, print_progress=print_test, device=device)
    #         test_loss.append(loss)
    #         test_accuracy.append(accuracy)
    #         test_steps.append(len(train_loss))
    #     return train_loss, train_accuracy, test_loss, test_accuracy, test_steps

        # def train_single_epoch_endd(model, teacher_ensemble, trainloader, criterion, optimizer, print_progress=True,
#                             device=None):
#     train_loss, train_accuracy = [], []
#
#     model.train()
#     running_loss = 0.0
#     for i, data in enumerate(trainloader, 0):
#         # Get inputs
#         inputs, labels = data
#         if device is not None:
#             inputs, labels = map(lambda x: x.to(device), (inputs, labels))
#
#         # zero the parameter gradients
#         optimizer.zero_grad()
#
#         model_logits = model(inputs)
#         ensemble_logits = teacher_ensemble(inputs)
#         loss = criterion(model_logits, ensemble_logits)
#         loss.backward()
#         optimizer.step()
#
#         # log statistics
#         train_loss.append(loss.item())
#         probs = F.softmax(model_logits, dim=1)
#         train_accuracy.append(calc_accuracy_torch(probs, labels, device).item())
#
#         # print statistics
#         running_loss += loss.item()
#         if (i + 1) % 10 == 0:
#             if print_progress:
#                 print(f'[Step: {i + 1}] loss: {running_loss / 10.0}')
#             running_loss = 0.0
#     return train_loss, train_accuracy
#
#
# def train_procedure_endd(model, teacher_ensemble, train_dataset, test_dataset, n_epochs=80, lr=0.001, lr_decay=0.9,
#                          batch_size=50,
#                          criterion=None,
#                          print_progress='test', device=None):
#     print_train, print_test = _get_print_progress_vars(print_progress)
#
#     if criterion is None:
#         criterion = EnDDSamplesLoss()
#     optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-6)
#     scheduler = torch.optim.lr_scheduler.ExponentialLR(optimizer, lr_decay, last_epoch=-1)
#
#     trainloader = DataLoader(train_dataset, batch_size=batch_size,
#                              shuffle=True, num_workers=1, drop_last=True)
#     testloader = DataLoader(test_dataset, batch_size=batch_size,
#                             shuffle=False, num_workers=1)
#
#     # Lists for storing training metrics
#     train_loss, train_accuracy = [], []
#     # Lists for storing test metrics
#     test_loss, test_accuracy, test_steps = [], [], []
#
#     for epoch in range(n_epochs):
#         if print_progress:
#             print(f"Epoch: {epoch}")
#         # Train
#         scheduler.step()
#         epoch_train_loss, epoch_train_accuracy = train_single_epoch_endd(model, teacher_ensemble, trainloader,
#                                                                          criterion, optimizer,
#                                                                          print_progress=print_train, device=device)
#         train_loss += epoch_train_loss
#         train_accuracy += epoch_train_accuracy
#         # Test
#         accuracy, loss = test(model, testloader, print_progress=print_test, device=device)
#         test_loss.append(loss)
#         test_accuracy.append(accuracy)
#         test_steps.append(len(train_loss))
#     return train_loss, train_accuracy, test_loss, test_accuracy, test_steps
#