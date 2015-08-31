'use strict';

/**
 * @ngdoc function
 * @name poligloMonitorApp.controller:WorkflowInstanceCtrl
 * @description
 * # WorkflowInstanceCtrl
 * Controller of the poligloMonitorApp
 */
angular.module('poligloMonitorApp')
    .controller('WorkflowsListCtrl', function ($scope, WorkflowInstance, Workflow) {
        Workflow.list(true, function(data){
            $scope.workflowGroups = data;
        });
    })
    .controller('WorkflowInstancesListCtrl', function ($scope, $stateParams, $interval, WorkflowInstance, Workflow) {
        $scope.workflowInstanceStatus = {};
        Workflow.get($stateParams.workflow, function(data){
            $scope.workflow = data;
        });
        var getStatus = function(statusId){
            WorkflowInstance.status(statusId, function(data){
                $scope.workflowInstanceStatus[statusId] = data.status;
            });
        };
        var updateWorkflowInstanceStatus = function(){
            for (var i = 0; i < $scope.workflowInstances.length; i++) {
                $scope.workflowInstances[i].creation_time_formatted = window.moment($scope.workflowInstances[i].creation_time*1000).fromNow();
                getStatus($scope.workflowInstances[i].id);

            }
        };

        var updateWorkflowInstancesList = function(){
            Workflow.listWorkflowInstances($stateParams.workflow, function(data){
                $scope.workflowInstances = data;
                updateWorkflowInstanceStatus();
            });
        };
        $scope.$on('$stateChangeStart',
            function(){
                $interval.cancel($scope.interval);
            }
        );
        $scope.interval = $interval(updateWorkflowInstancesList, 1000);
    })
    .controller('WorkflowInstanceShowCtrl', function ($scope, $stateParams, $interval, WorkflowInstance, Workflow) {
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
            }
            $scope.workers.push(connections[i-1].data.target);
        };

        var updateStats = function(){
            WorkflowInstance.stats($stateParams.workflowInstanceId, function(data){
                $scope.workflowInstanceStats = data;
                if($scope.workflowInstanceStats.start_time){
                    $scope.workflowInstanceStats.start_time_formatted = window.moment(
                        $scope.workflowInstanceStats.start_time*1000
                    ).fromNow();
                }else{
                    $scope.workflowInstanceStats.start_time_formatted = 'pending';
                }
            });
        };

        WorkflowInstance.get($stateParams.workflowInstanceId, function(data){
            $scope.workflowInstance = data;
            Workflow.get($scope.workflowInstance.type, function(data){
                $scope.workflow = data;
                getWorkers();
                updateStats();
            });
        });
        $scope.$on('$stateChangeStart',
            function(){
                $interval.cancel($scope.interval);
            }
        );
        $scope.interval = $interval(updateStats, 1000);

    }).controller('WorkflowInstanceWorkerErrorsCtrl', function ($scope, $stateParams, WorkflowInstance) {
        $scope.workerId = $stateParams.workerId;
        $scope.discardError = function(index){
            WorkflowInstance.discardError(
                $scope.workflowInstance.id, $stateParams.workerId, $scope.errors[index].redis_score,
                function(data){
                    updateErrors();
                }
            );
        };
        $scope.retryError = function(index){
            WorkflowInstance.retryError(
                $scope.workflowInstance.id, $stateParams.workerId, $scope.errors[index].redis_score,
                function(data){
                    updateErrors();
                }
            );
        };
        $scope.retryAllErrors = function(){
            WorkflowInstance.retryAllErrors(
                $scope.workflowInstance.id, $stateParams.workerId,
                function(){
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
