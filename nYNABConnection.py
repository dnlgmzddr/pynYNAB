# coding=utf-8
import mechanize
import logging
import json
import uuid
import pickle
import requests
from requests.cookies import RequestsCookieJar
import os
from config import appdir
from Entity import ComplexEncoder
from utils import RateLimited

logger=logging.getLogger('pynYNAB')

class NYnabConnectionError(Exception):
    pass


class nYnabConnection(object):
    url = 'https://app.youneedabudget.com/users/login'
    urlCatalog = 'https://app.youneedabudget.com/api/v1/catalog'
    sessionpath = os.path.join(appdir.user_data_dir, 'session')

    def getsession(self):
        self.session.cookies = RequestsCookieJar()
        self.browser.open(self.url)

        self.session.headers['X-YNAB-Device-Id'] = self.id
        self.session.headers['User-Agent'] = 'python nYNAB API bot - rienafairefr rienafairefr@gmail.com'

        firstlogin = self.dorequest({"email": self.email, "password": self.password, "remember_me": True,
                                     "device_info": {"id": self.id}}, 'loginUser')
        self.sessionToken = firstlogin["session_token"]
        self.session.headers['X-Session-Token'] = self.sessionToken

    def loadsession(self):
        with open(self.sessionpath, 'r') as file:
            self.session = pickle.load(file)
            self.sessionToken = self.session.headers['X-Session-Token']
            self.id = self.session.headers['X-YNAB-Device-Id']

    def savesession(self):
        with open(self.sessionpath, 'w') as file:
            pickle.dump(self.session, file)


    def __init__(self, email, password, reload=False):
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.browser = mechanize.Browser()
        self.browser.set_handle_robots(False)
        self.id = str(uuid.uuid3(uuid.NAMESPACE_DNS, 'rienafairefr.pynYNAB'))
        self.lastrequest_elapsed=None

        if reload:
            self.getsession()
        else:
            try:
                self.loadsession()
            except:
                self.getsession()
        self.savesession()

    @RateLimited(maxPerSecond=1)
    def dorequest(self, request_dic, opname):
        # Available operations : loginUser,getInitialUserData,logoutUser,createNewBudget,freshStartABudget,cloneBudget,
        # deleteTombstonedBudgets,syncCatalogData,syncBudgetData,getInstitutionList
        # getInstitutionLoginFields,getInstitutionAccountList,registerAccountForDirectConnect,
        # updateDirectConnectCredentials,poll,createFeedback,runSqlStatement

        params = { u'operation_name': opname,'request_data': json.dumps(request_dic, cls=ComplexEncoder),}
        logger.debug('POST-ing ...',params)
        r = self.session.post(self.urlCatalog, params, verify=False)
        self.lastrequest_elapsed=r.elapsed
        js = r.json()
        if r.status_code != 200:
            logger.debug(r.text)
            raise NYnabConnectionError('non-200 HTTP code returned from the API')
        if js['error'] is None:
            return js
        else:
            raise NYnabConnectionError('Error was returned from the API')












