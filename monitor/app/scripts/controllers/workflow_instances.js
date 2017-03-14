'use strict';

/**
 * @ngdoc function
 * @name poligloMonitorApp.controller:WorkflowInstanceCtrl
 * @description
 * # WorkflowInstanceCtrl
 * Controller of the poligloMonitorApp
 */
angular.module('poligloMonitorApp')
    .controller('WorkflowsListCtrl', function ($scope, WorkflowInstance, Workflow, Flash) {
        Workflow.list(true, function(data){
            $scope.workflowGroups = data;
        }, function(data, status) {
            var message = "Error connecting to Poliglo server. Status: " + status;
            Flash.create('danger', message, 0);
        });
    })
    .controller('WorkflowInstancesListCtrl', function ($scope, $stateParams, $interval, WorkflowInstance, Workflow) {
        $scope.workflowInstanceStatus = {};
        $scope.loading = true;
        Workflow.get($stateParams.workflow, function(data){
            $scope.workflow = data;
        });
        var getStatus = function(statusId){
            WorkflowInstance.status(statusId, function(data){
                $scope.workflowInstanceStatus[statusId] = data;
            });
        };
        var updateWorkflowInstanceStatus = function(){
            for (var i = 0; i < $scope.workflowInstances.length; i++) {
                $scope.workflowInstances[i].creation_time_human = window.moment($scope.workflowInstances[i].creation_time*1000).format();
                $scope.workflowInstances[i].creation_time_formatted = window.moment($scope.workflowInstances[i].creation_time*1000).fromNow();
                var status_data = $scope.workflowInstanceStatus[$scope.workflowInstances[i].id];
                if(status_data && status_data.status === 'done')
                    continue;
                getStatus($scope.workflowInstances[i].id);

            }
        };

        var updateWorkflowInstancesList = function(){
            Workflow.listWorkflowInstances($stateParams.workflow, function(data){
                $scope.loading = false;
                $scope.workflowInstances = data;
                updateWorkflowInstanceStatus();
            });
        };
        $scope.$on('$stateChangeStart',
            function(){
                $interval.cancel($scope.interval);
            }
        );
        updateWorkflowInstancesList();
        $scope.interval = $interval(updateWorkflowInstancesList, 3000);
    })
    .controller('WorkflowInstanceShowCtrl', function ($scope, $rootScope, $stateParams, $interval, $document, WorkflowInstance, Workflow, Supervisor) {
        $scope.getSupervisorStatus = function(){
            Workflow.supervisorStatus($scope.workflow.id, function(data){
                $scope.supervisorStatus = data;
            });
        };
        $scope.stopProcess = function(processName){
            Supervisor.stopProcess(processName, function(data){
                $scope.getSupervisorStatus();
            })
        };
        $scope.startProcess = function(processName){
            Supervisor.startProcess(processName, function(data){
                $scope.getSupervisorStatus();
            })
        };
        // graph
        $scope.elements = [];
        $scope.edges = [];
        var drawGraph = function(){
            $rootScope.$broadcast('appChanged');
        }

        var getConnections = function(workers, nodeId){
            var connections = [];
            var worker = getWorker(workers, nodeId);
            if(worker && worker.next_workers){
                connections = connections.concat(worker.next_workers);
            }
            return connections;
        };

        var getWorker = function(workers, nodeId){
            return workers[nodeId];
        };

        var getEdges = function(startNode, workers){
            var missingNodes = [startNode];
            var edges = [];
            for (var i = 0; i < missingNodes.length; i++) {
                var connections = getConnections(workers, missingNodes[i]);
                for (var j = 0; j < connections.length; j++) {
                    if(missingNodes.indexOf(connections[j]) <0){
                        missingNodes.push(connections[j]);
                    }
                    if(getWorker(workers, missingNodes[i]) && getWorker(workers, connections[j])){
                        edges.push(
                            { data: { id: missingNodes[i]+'_'+ connections[j], weight: 1, source: missingNodes[i], target: connections[j] } }
                        );
                    }
                }
            }
            return edges;
        };

        var getWorkers = function(){
            var connections = getEdges(
                $scope.workflow.start_worker_id,
                $scope.workflow.workers
            );
            $scope.workers = [];
            var i = 0;
            for (; i < connections.length; i++) {
                $scope.workers.push(connections[i].data.source);
                var edge = {
                    id: 'edge'+i,
                    source: connections[i].data.source,
                    target: connections[i].data.target
                };
                $scope.edges.push(edge);
            }
            $scope.workers.push(connections[i-1].data.target);
            $scope.workers = $.unique($scope.workers);
        };

        var updateStats = function(){
            $scope.getSupervisorStatus();
            WorkflowInstance.stats($stateParams.workflowInstanceId, function(data){
                $scope.workflowInstanceStats = data;
                if($scope.workflowInstanceStats.start_time){
                    $scope.workflowInstanceStats.start_time_human = window.moment(
                        $scope.workflowInstanceStats.start_time*1000
                    ).format()
                    $scope.workflowInstanceStats.start_time_formatted = window.moment(
                        $scope.workflowInstanceStats.start_time*1000
                    ).fromNow();
                }else{
                    $scope.workflowInstanceStats.start_time_formatted = 'pending';
                    $scope.workflowInstanceStats.start_time_human = 'pending';
                }
            });
        };

        WorkflowInstance.get($stateParams.workflowInstanceId, function(data){
            $scope.workflowInstance = data;
            Workflow.get($scope.workflowInstance.type, function(data){
                $scope.workflow = data;
                getWorkers();
                updateStats();
                $scope.workers.forEach(function(worker){
                    $scope.elements.push({id: worker});
                });
                drawGraph();
            });
        });
        $scope.$on('$stateChangeStart',
            function(){
                $interval.cancel($scope.interval);
            }
        );
        $scope.interval = $interval(updateStats, 3000);

    }).controller('WorkflowInstanceWorkerErrorsCtrl', function ($scope, $stateParams, WorkflowInstance, Flash) {
        $scope.workerId = $stateParams.workerId;
        $scope.discardError = function(index){
            WorkflowInstance.discardError(
                $scope.workflowInstance.id, $stateParams.workerId, $scope.errors[index].redis_score,
                function(data){
                    Flash.create('warning', 'Task discarded');
                    updateErrors();
                }
            );
        };
        $scope.retryError = function(index){
            WorkflowInstance.retryError(
                $scope.workflowInstance.id, $stateParams.workerId, $scope.errors[index].redis_score,
                function(data){
                    Flash.create('success', 'Task successfully started');
                    updateErrors();
                }
            );
        };
        $scope.retryAllErrors = function(){
            WorkflowInstance.retryAllErrors(
                $scope.workflowInstance.id, $stateParams.workerId,
                function(){
                    Flash.create('success', 'Task successfully started');
                    updateErrors();
                }
            );
        };
        var updateErrors = function(){
            WorkflowInstance.workerErrors(
                $stateParams.workflowInstanceId, $stateParams.workerId, function(data){
                    $scope.errors = data;
                }
            );
        };

        $scope.tidyJSON = function(obj){
            return JSON.stringify(obj, null, 2);
        };

        WorkflowInstance.get($stateParams.workflowInstanceId, function(data){
            $scope.workflowInstance = data;
            updateErrors();

        });
    }).controller('WorkflowInstanceWorkerFinalizedCtrl', function ($scope, $stateParams, WorkflowInstance) {
        $scope.workerId = $stateParams.workerId;

        var updateFinalized = function(){
            WorkflowInstance.workerFinalized(
                $stateParams.workflowInstanceId, $stateParams.workerId, function(data){
                    $scope.finalized = data;
                }
            );
        };

        $scope.tidyJSON = function(obj){
            return JSON.stringify(obj, null, 2);
        };

        WorkflowInstance.get($stateParams.workflowInstanceId, function(data){
            $scope.workflowInstance = data;
            updateFinalized();
        });
    });
