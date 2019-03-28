﻿# QUANTCONNECT.COM - Democratizing Finance, Empowering Individuals.
# Lean Algorithmic Trading Engine v2.0. Copyright 2014 QuantConnect Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from clr import AddReference
AddReference("QuantConnect.Common")
AddReference("QuantConnect.Algorithm")

from QuantConnect import *
from QuantConnect.Algorithm import *
from QuantConnect.Algorithm.Framework import *
from QuantConnect.Algorithm.Framework.Alphas import AlphaModel, Insight, InsightType, InsightDirection


class ConstantAlphaModel(AlphaModel):
    ''' Provides an implementation of IAlphaModel that always returns the same insight for each security'''

    def __init__(self, type, direction, period, magnitude = None, confidence = None):
        '''Initializes a new instance of the ConstantAlphaModel class
        Args:
            type: The type of insight
            direction: The direction of the insight
            period: The period over which the insight with come to fruition
            magnitude: The predicted change in magnitude as a +- percentage
            confidence: The confidence in the insight'''
        self.type = type
        self.direction = direction
        self.period = period
        self.magnitude = magnitude
        self.confidence = confidence
        self.securities = []
        self.insightsTimeBySymbol = {}

        typeString = Extensions.GetEnumString(type, InsightType)
        directionString = Extensions.GetEnumString(direction, InsightDirection)

        self.Name = '{}({},{},{}'.format(self.__class__.__name__, typeString, directionString, strfdelta(period))
        if magnitude is not None:
            self.Name += ',{}'.format(magnitude)
        if confidence is not None:
            self.Name += ',{}'.format(confidence)

        self.Name += ')';


    def Update(self, algorithm, data):
        ''' Creates a constant insight for each security as specified via the constructor
        Args:
            algorithm: The algorithm instance
            data: The new data available
        Returns:
            The new insights generated'''
        insights = []

        for security in self.securities:
            if self.ShouldEmitInsight(algorithm.UtcTime, security.Symbol):
                insights.append(Insight(security.Symbol, self.period, self.type, self.direction, self.magnitude, self.confidence))

        return insights


    def OnSecuritiesChanged(self, algorithm, changes):
        ''' Event fired each time the we add/remove securities from the data feed
        Args:
            algorithm: The algorithm instance that experienced the change in securities
            changes: The security additions and removals from the algorithm'''
        for added in changes.AddedSecurities:
            self.securities.append(added)

        # this will allow the insight to be re-sent when the security re-joins the universe
        for removed in changes.RemovedSecurities:
            if removed in self.securities:
                self.securities.remove(removed)
            if removed.Symbol in self.insightsTimeBySymbol:
                self.insightsTimeBySymbol.pop(removed.Symbol)


    def ShouldEmitInsight(self, utcTime, symbol):

        generatedTimeUtc = self.insightsTimeBySymbol.get(symbol)

        if generatedTimeUtc is not None:
            # we previously emitted a insight for this symbol, check it's period to see
            # if we should emit another insight
            if utcTime - generatedTimeUtc < self.period:
                return False

        # we either haven't emitted a insight for this symbol or the previous
        # insight's period has expired, so emit a new insight now for this symbol
        self.insightsTimeBySymbol[symbol] = utcTime
        return True

def strfdelta(tdelta):
    d = tdelta.days
    h, rem = divmod(tdelta.seconds, 3600)
    m, s = divmod(rem, 60)
    return "{}.{:02d}:{:02d}:{:02d}".format(d,h,m,s)