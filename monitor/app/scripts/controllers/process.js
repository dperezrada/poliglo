'use strict';

/**
 * @ngdoc function
 * @name poligloMonitorApp.controller:ProcessCtrl
 * @description
 * # ProcessCtrl
 * Controller of the poligloMonitorApp
 */
angular.module('poligloMonitorApp')
    .controller('ScriptsListCtrl', function ($scope, Process, Script) {
        Script.list(true, function(data){
            $scope.scriptGroups = data;
        });
    })
    .controller('ProcessesListCtrl', function ($scope, $stateParams, $interval, Process, Script) {
            $scope.processStatus = {};
            Script.get($stateParams.scriptType, function(data){
                $scope.script = data;
            });
            var getStatus = function(statusId){
                Process.status(statusId, function(data){
                    $scope.processStatus[statusId] = data.status;
                });
            };
            var updateProcessStatus = function(){
                for (var i = 0; i < $scope.processes.length; i++) {
                    $scope.processes[i].start_time_formatted = window.moment($scope.processes[i].start_time*1000).fromNow();
                    getStatus($scope.processes[i].id);

                }
            };

            var updateProcesessList = function(){
                Script.listProcesses($stateParams.scriptType, function(data){
                    $scope.processes = data;
                    updateProcessStatus();
                });
            };
            $scope.$on('$stateChangeStart',
                function(){
                    $interval.cancel($scope.interval);
                }
            );
            $scope.interval = $interval(updateProcesessList, 1000);


    }).controller('ProcessShowCtrl', function ($scope, $stateParams, $interval, Process, Script) {
        var getConnections = function(workers, nodeId){
            var connections = [];
            var worker = getWorker(workers, nodeId);
            if(worker && worker.next_workers){
                connections = connections.concat(worker.next_workers);
            }
            return connections;
        };

        var getWorker = function(workers, nodeId){
            return _.findWhere(workers, {id: nodeId});
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
                $scope.script.start_worker_id,
                $scope.script.workers
            );
            $scope.workers = [];
            var i = 0;
            for (; i < connections.length; i++) {
                $scope.workers.push(connections[i].data.source);
            }
            $scope.workers.push(connections[i-1].data.target);
        };

        var updateStats = function(){
            Process.stats($stateParams.processId, function(data){
                $scope.processStats = data;
            });
        };

        Process.get($stateParams.processId, function(data){
            $scope.process = data;
            Script.get($scope.process.type, function(data){
                $scope.script = data;
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

    }).controller('ProcessWorkerErrorsCtrl', function ($scope, $stateParams, Process) {
        $scope.workerId = $stateParams.workerId;
        $scope.discardError = function(index){
            Process.discardError(
                $scope.process.id, $stateParams.workerId, $scope.errors[index].redis_score,
                function(data){
                    updateErrors();
                }
            );
        };
        $scope.retryError = function(index){
            Process.retryError(
                $scope.process.id, $stateParams.workerId, $scope.errors[index].redis_score,
                function(data){
                    updateErrors();
                }
            );
        };
        $scope.retryAllErrors = function(){
            Process.retryAllErrors(
                $scope.process.id, $stateParams.workerId,
                function(){
                    updateErrors();
                }
            );
        };
        var updateErrors = function(){
            Process.workerErrors(
                $stateParams.processId, $stateParams.workerId, function(data){
                    $scope.errors = data;
                }
            );
        };

        Process.get($stateParams.processId, function(data){
            $scope.process = data;
            updateErrors();

        });
    }).controller('ProcessWorkerFinalizedCtrl', function ($scope, $stateParams, Process) {
        $scope.workerId = $stateParams.workerId;

        var updateFinalized = function(){
            Process.workerFinalized(
                $stateParams.processId, $stateParams.workerId, function(data){
                    $scope.finalized = data;
                }
            );
        };

        $scope.tidyJSON = function(obj){
            return JSON.stringify(obj, null, 2);
        };

        Process.get($stateParams.processId, function(data){
            $scope.process = data;
            updateFinalized();
        });
    });
