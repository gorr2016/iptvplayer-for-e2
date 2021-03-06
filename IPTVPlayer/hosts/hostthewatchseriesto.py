# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSearchHistoryHelper, GetDefaultLang, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
###################################################

###################################################
# FOREIGN import
###################################################
from datetime import timedelta
import time
import re
import urllib
import unicodedata
import base64
try:    import json
except: import simplejson as json
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################


###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################

def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'http://thewatchseries.to/'

class TheWatchseriesTo(CBaseHostClass):
    HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
    AJAX_HEADER = dict(HEADER)
    AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
    
    MAIN_URL      = 'http://thewatchseries.to/'
    SEARCH_URL    = MAIN_URL + 'search/'
    DEFAULT_ICON  = "http://thewatchseries.to/templates/default/images/logo.png"
    
    MAIN_CAT_TAB = [{'icon':DEFAULT_ICON, 'category':'list_series',     'title': _('Series list'),           'url':MAIN_URL+'series'},
                    {'icon':DEFAULT_ICON, 'category':'episodes',        'title': _('Popular Episodes'),      'url':MAIN_URL+'new'},
                    {'icon':DEFAULT_ICON, 'category':'episodes',        'title': _('Newest Episodes'),       'url':MAIN_URL+'latest'},
                    {'icon':DEFAULT_ICON, 'category':'categories',      'title': _('All A-Z'),               'url':MAIN_URL+'letters/A'},
                    {'icon':DEFAULT_ICON, 'category':'categories',      'title': _('Genres'),                'url':MAIN_URL+'genres/action'},
                    {'icon':DEFAULT_ICON, 'category':'search',          'title': _('Search'), 'search_item':True},
                    {'icon':DEFAULT_ICON, 'category':'search_history',  'title': _('Search history')} ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'  TheWatchseriesTo.tv', 'cookie':'thewatchseriesto.cookie'})
        self.defaultParams = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        self.seasonCache = {}
        self.cacheLinks = {}
        
    def _getFullUrl(self, url):
        if url.startswith('//'):
            url = 'http:' + url
        elif url.startswith('/'):
            url = self.MAIN_URL + url[1:]
        elif 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        
        if not self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
                
        url = self.cleanHtmlStr(url)
        url = self.replacewhitespace(url)

        return url
        
    def cleanHtmlStr(self, data):
        data = data.replace('&nbsp;', ' ')
        data = data.replace('&nbsp', ' ')
        return CBaseHostClass.cleanHtmlStr(data)
        
    def replacewhitespace(self, data):
        data = data.replace(' ', '%20')
        return CBaseHostClass.cleanHtmlStr(data)

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("TheWatchseriesTo.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def listCategories(self, cItem, nextCategory):
        printDBG("TheWatchseriesTo.listCategories")
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="pagination"', '</ul>', False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
        
        for item in data:
            url = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''', 1)[0]
            url = self._getFullUrl( url )
            if not url.startswith('http') or 'latest' in url: continue
            title = self.cleanHtmlStr(item)
            params = dict(cItem)
            params.update({'category':nextCategory, 'title':title, 'url':url, 'page':0})
            self.addDir(params)
            
    def listItems(self, cItem, nextCategory):
        printDBG("TheWatchseriesTo.listItems")
        page      = cItem.get('page', 1)
        post_data = cItem.get('post_data', None) 
        url       = cItem['url']
        
        if cItem.get('page', 0) > 0:
            if not url.endswith('/'):
                url += '/'
            if '/search/' in url:
                url += 'page/'
            url += '%d' % page
        
        sts, data = self.cm.getPage(url, {}, post_data)
        if not sts: return
        
        nextPage = self.cm.ph.getAllItemsBeetwenMarkers(data, '<ul class="pagination"', '</ul>', False)
        if len(nextPage):
            nextPage = nextPage[-1]
        else: nextPage = ''
        if '>{0}<'.format(page + 1) in nextPage:
            nextPage = True
        else: nextPage = False
        
        mainMarker = '<ul class="listings">'
        if mainMarker in data:
            data = self.cm.ph.getDataBeetwenMarkers(data, mainMarker, '<br class="clear"')[1]
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li', '</li>')
            ta = False
        else:
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div style="float:left; width:639px;">', 'Latest Episode:', False)
            ta = True
        for item in data:
            icon  = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            icon = self._getFullUrl(icon)
            if icon == '': icon = cItem['icon']
            if ta: item = item.split('<div valign="top" style="padding-left: 10px;">')[-1]
            if 'category-item-ad' in item or 'Latest Episode' in item: continue
            url = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
            if url == '': continue
            title = self.cm.ph.getSearchGroups(item, '''title=['"]([^'^"]+?)['"]''')[0]
            if title == '': title = item.split('<span class="epnum"')[0]
            desc = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(item, '<div class="info">', '</div>', False)[1] )
            if desc == '': desc = self.cleanHtmlStr(item)
            
            params = dict(cItem)
            params.update({'category':nextCategory, 'title':self.cleanHtmlStr(title), 'url':self._getFullUrl(url), 'icon':icon, 'desc':desc})
            
            if nextCategory == 'video' or '/episode/' in url:
                self.addVideo(params)
            else:
                self.addDir(params)
        if nextPage:
                params = dict(cItem)
                params.update({'title':_('Next page'), 'page':page+1})
                self.addDir(params)
        
    def listSeasons(self, cItem, nextCateogry):
        printDBG("TheWatchseriesTo.listSeasons")
        self.seasonCache = {}
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return
        
        seasons = self.cm.ph.getAllItemsBeetwenMarkers(data, '<h2 class="lists"', '</ul>')
        for season in seasons:
            seasonName = self.cleanHtmlStr( self.cm.ph.getDataBeetwenMarkers(season, 'itemprop="name">', '</span>', False)[1] )
            seasonNum = self.cm.ph.getSearchGroups(seasonName+'|', '''Season\s+?([0-9]+?)[^0-9]''', 1, True)[0]
            
            episodesTab = []
            data = self.cm.ph.getAllItemsBeetwenMarkers(season, '<li ', '</li>')
            for item in data:
                if '(0 links)' in item: continue
                title = self.cleanHtmlStr( self.cm.ph.getDataBeetwenReMarkers(item, re.compile('itemprop="name"[^>]*?>'), re.compile('</span>'), False)[1] )
                url = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
                episodeNum = self.cm.ph.getSearchGroups(title + '|', '''Episode\s+?([0-9]+?)[^0-9]''', 1, True)[0]
                printDBG(">>>>>>>>>>>>>>>>>>>>>>>> e[%s] s[%s]" % (episodeNum, seasonNum) )
                if '' != episodeNum and '' != seasonNum:
                    title = 's%se%s'% (seasonNum.zfill(2), episodeNum.zfill(2)) + ' - ' + title.replace('Episode %s' % episodeNum, '')
                params = dict(cItem)
                params.update({'title':'{0}: {1}'.format(cItem['title'], title), 'url':self._getFullUrl(url), 'desc':self.cleanHtmlStr(item)})
                episodesTab.append(params)
            
            if len(episodesTab):
                self.seasonCache[seasonName] = episodesTab
                params = dict(cItem)
                params.update({'category':nextCateogry, 'title':seasonName, 'season_key':seasonName})
                self.addDir(params)
                
    def listEpisodes(self, cItem):
        printDBG("TheWatchseriesTo.listEpisodes")
        tab = self.seasonCache.get(cItem['season_key'], [])
        self.listsTab(tab, cItem, 'video')
            
    def getLinksForVideo(self, cItem):
        printDBG("TheWatchseriesTo.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        if len(self.cacheLinks.get(cItem['url'], [])):
            return self.cacheLinks[cItem['url']]
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return []
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<tr class="download_link_', '</tr>')
        for item in data:
            host = self.cm.ph.getSearchGroups(item, '''"download_link_([^'^"]+?)['"]''')[0]
            #if self.up.checkHostSupport('http://'+host+'/') != 1: continue
            url = self.cm.ph.getSearchGroups(item, '''href=['"][^'^"]*?\?r=([^'^"]+?)['"][^>]*?buttonlink''')[0]
            if url == '': continue
            try:
                url = base64.b64decode(url)
            except:
                printExc()
                continue
            if self.up.checkHostSupport(url) != 1: continue
            urlTab.append({'name':host, 'url':self._getFullUrl(url), 'need_resolve':1})
        if len(urlTab):
            self.cacheLinks[cItem['url']] = urlTab
        return urlTab
        
    def getVideoLinks(self, videoUrl):
        printDBG("TheWatchseriesTo.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        for key in self.cacheLinks:
            for idx in range(len(self.cacheLinks[key])):
                if self.cacheLinks[key][idx]['url'] == videoUrl:
                    self.cacheLinks[key][idx]['name'] = '*' + self.cacheLinks[key][idx]['name']
        
        if videoUrl.startswith('http'):
            urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("TheWatchseriesTo.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        cItem = dict(cItem)
        cItem['url'] = self.SEARCH_URL + urllib.quote(searchPattern)
        self.listItems(cItem, 'list_seasons')
        
    def getFavouriteData(self, cItem):
        printDBG("TheWatchseriesTo.getFavouriteData")
        return str(cItem['url'])
        
    def getLinksForFavourite(self, fav_data):
        printDBG("TheWatchseriesTo.getLinksForFavourite")
        return self.getLinksForVideo(self, {'url':fav_data})

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
        elif category == 'categories':
            self.listCategories(self.currItem, 'list_series')
        elif category == 'list_series':
            self.listItems(self.currItem, 'list_seasons')
        elif category == 'list_seasons':
            self.listSeasons(self.currItem, 'list_episodes')
        elif category == 'list_episodes':
            self.listEpisodes(self.currItem)
        elif category == 'episodes':
            self.listItems(self.currItem, 'video')
        elif category == 'list_items':
            self.listItems(self.currItem)
    #SEARCH
        elif category in ["search", "search_next_page"]:
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category'}) 
            self.listSearchResult(cItem, searchPattern, searchType)
    #HISTORIA SEARCH
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()
        
        CBaseHostClass.endHandleService(self, index, refresh)
class IPTVHost(CHostBase):

    def __init__(self):
        # for now we must disable favourites due to problem with links extraction for types other than movie
        CHostBase.__init__(self, TheWatchseriesTo(), True, favouriteTypes=[CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('thewatchseriestologo.png')])
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], item['need_resolve']))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
    def getResolvedURL(self, url):
        # resolve url to get direct url to video file
        retlist = []
        urlList = self.host.getVideoLinks(url)
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        #searchTypesOptions.append((_("Movies"),   "movie"))
        #searchTypesOptions.append((_("TV Shows"), "tv_shows"))
        
        hostLinks = []
        type = CDisplayListItem.TYPE_UNKNOWN
        possibleTypesOfSearch = None

        if 'category' == cItem['type']:
            if cItem.get('search_item', False):
                type = CDisplayListItem.TYPE_SEARCH
                possibleTypesOfSearch = searchTypesOptions
            else:
                type = CDisplayListItem.TYPE_CATEGORY
        elif cItem['type'] == 'video':
            type = CDisplayListItem.TYPE_VIDEO
        elif 'more' == cItem['type']:
            type = CDisplayListItem.TYPE_MORE
        elif 'audio' == cItem['type']:
            type = CDisplayListItem.TYPE_AUDIO
            
        if type in [CDisplayListItem.TYPE_AUDIO, CDisplayListItem.TYPE_VIDEO]:
            url = cItem.get('url', '')
            if '' != url:
                hostLinks.append(CUrlItem("Link", url, 1))
            
        title       =  cItem.get('title', '')
        description =  cItem.get('desc', '')
        icon        =  cItem.get('icon', '')
        
        return CDisplayListItem(name = title,
                                    description = description,
                                    type = type,
                                    urlItems = hostLinks,
                                    urlSeparateRequest = 1,
                                    iconimage = icon,
                                    possibleTypesOfSearch = possibleTypesOfSearch)
    # end converItem

    def getSearchItemInx(self):
        try:
            list = self.host.getCurrList()
            for i in range( len(list) ):
                if list[i]['category'] == 'search':
                    return i
        except:
            printDBG('getSearchItemInx EXCEPTION')
            return -1

    def setSearchPattern(self):
        try:
            list = self.host.getCurrList()
            if 'history' == list[self.currIndex]['name']:
                pattern = list[self.currIndex]['title']
                search_type = list[self.currIndex]['search_type']
                self.host.history.addHistoryItem( pattern, search_type)
                self.searchPattern = pattern
                self.searchType = search_type
        except:
            printDBG('setSearchPattern EXCEPTION')
            self.searchPattern = ''
            self.searchType = ''
        return
