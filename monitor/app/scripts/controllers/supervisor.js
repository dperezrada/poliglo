'use strict';

angular.module('poligloMonitorApp')
  .controller('SupervisorStatusCtrl', function($scope, Supervisor) {
    $scope.loading = true;
    $scope.supervisorStatus = '';
    $scope.updatedAt = '';
    $scope.getStatus = function(){
      Supervisor.status(function(data){
        $scope.data = data;
        $scope.loading = false;
        $scope.supervisorStatus = 'running';
        $scope.updatedAt = new Date();
      }, function(data){
        $scope.data = null;
        $scope.loading = false;
        $scope.supervisorStatus = 'stopped';
        $scope.updatedAt = new Date();
      });
    };
    $scope.stopProcess = function(processName){
      Supervisor.stopProcess(processName, function(data){
        $scope.getStatus();
      })
    };
    $scope.startProcess = function(processName){
      Supervisor.startProcess(processName, function(data){
        $scope.getStatus();
      })
    };
    $scope.getStatus();
  });
