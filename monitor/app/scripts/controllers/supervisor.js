'use strict';

angular.module('poligloMonitorApp')
  .controller('SupervisorStatusCtrl', function($scope, Supervisor) {
    Supervisor.status(function(data){
      $scope.data = data;
    });
  });
