# -*- coding: utf-8 -*-
#
# -*- Coded  by gorr -*-
#
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.moonwalkcc import MoonwalkParser
###################################################
# FOREIGN import
###################################################
import re
import urllib
###################################################
# E2 GUI COMMPONENTS
###################################################
# Config options for HOST
###################################################


def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'Kinotan'


class Kinotan(CBaseHostClass):

    MAIN_URL = 'http://kinotan.ru/'
    DEFAULT_ICON_URL = 'http://ipic.su/img/img7/fs/logo2.1460442551.png'
    SRCH_URL = MAIN_URL + '?do = search & mode = advanced & subaction = search & story ='
    SERIES_URL = MAIN_URL + 'serial/'


    MAIN_CAT_TAB = [dict(category='cat_serials', title=_('Serials'), icon=DEFAULT_ICON_URL, url=SERIES_URL),
                    dict(category='cat_tv_shows', title=_('TV shows'), icon=DEFAULT_ICON_URL, url=MAIN_URL + 'tv-shou/'),
                    dict(category='cat_mult', title=_('Cartoons'), icon=DEFAULT_ICON_URL, url=MAIN_URL + 'multserial/'),
                    dict(category='search', title=_('Search'), search_item=True),
                    dict(category='search_history', title=_('Search history'))]

    SERIALS_CAT_TAB = [dict(category='genre', title=_('Genre selection'), icon=DEFAULT_ICON_URL, url=SERIES_URL),
                       dict(category='country', title=_('By country'), icon=DEFAULT_ICON_URL, url=SERIES_URL),
                       dict(category='trans', title=_('Translations'), icon=DEFAULT_ICON_URL, url=SERIES_URL),
                       dict(category='sel', title=_('Collections'), icon=DEFAULT_ICON_URL, url=SERIES_URL),
                       dict(category='years', title=_('By Year'), icon=DEFAULT_ICON_URL, url=SERIES_URL)]

    def __init__(self):
        CBaseHostClass.__init__(self, {'history': 'Kinotan', 'cookie': 'Kinotan.cookie'})
        self.moonwalkParser = MoonwalkParser()

    def _getFullUrl(self, url):
        mainUrl = self.MAIN_URL
        if 0 < len(url) and not url.startswith('http'):
            if url.startswith('/'):
                url = url[1:]
            url = mainUrl + url
        if not mainUrl.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url

    def getPage(self, url, params={}, post_data=None):
        sts, data = self.cm.getPage(url, params, post_data)
        return sts, data

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("Kinotan.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name'] = 'category'
            if type == 'dir':
                self.addDir(params)
            else:
                self.addVideo(params)

    def listMainMenu(self, cItem, category):
        printDBG("Kinotan.listCategories")
        sts, data = self.getPage(cItem['url'])
        if not sts: return

        datac = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="head-menu">', '</ul>', False)[1]
        datac = re.compile('<a[^"]+?href="(.*?)".*>(.*?)</a></li>').findall(datac)
        for item in datac:
            if item[0] in ['/novosti/', 'http://kinotan.ru/skoro/',
                           'http://kinotan.ru/index.php?do=orderdesc']: continue
        params = dict(cItem)
        params.update({'category': category, 'title': item[1], 'url': self._getFullUrl(item[0])})
        self.addDir(params)
        self.listsTab(self.MAIN_CAT_TAB, {'name': 'category'})

    def listGenre(self, cItem, category):
        printDBG("Kinotan.listGenre")
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        datag = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="main-menu clearfix">', '</ul>', False)[1]
        datag = re.compile('<a[^"]+?href="(.*?)">(.*?)</a></li>').findall(datag)
        for item in datag:
            params = dict(cItem)
            params.update({'category': category, 'title': item[1], 'url': self._getFullUrl(item[0])})
            self.addDir(params)

    def listCountry(self, cItem, category):
        printDBG("Kinotan.listCountry")
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        datacn = self.cm.ph.getDataBeetwenMarkers(data, '<div class="navigright2">', '</div>', False)[1]
        datacn = re.compile('href="(/xf.*?)">(.*?)</a><br>').findall(datacn)
        for item in datacn:
            params = dict(cItem)
            params.update({'category': category, 'title': item[1], 'url': self._getFullUrl(item[0][1:])})
            self.addDir(params)

    def listTrans(self, cItem, category):
        printDBG("Kinotan.listTrans")
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        datatr = self.cm.ph.getDataBeetwenMarkers(data, '<div class="navigright3">', '</div>', False)[1]
        datatr = re.compile('href="(/xf.*?)">(.*?)</a><br>').findall(datatr)
        for item in datatr:
            params = dict(cItem)
            params.update({'category': category, 'title': item[1], 'url': self._getFullUrl(item[0][1:])})
            self.addDir(params)

    def listSel(self, cItem, category):
        printDBG("Kinotan.listSel")
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        data1 = self.cm.ph.getDataBeetwenMarkers(data, '<div class="navigright">', '</div>', False)[1]
        datasl = re.compile('href="(/xf.*?)">(.*?)</a><br>').findall(data1)
        for item in datasl:
            params = dict(cItem)
            params.update({'category': category, 'title': item[1], 'url': self._getFullUrl(item[0][1:])})
            self.addDir(params)

    def listYears(self, cItem, category):
        printDBG("Kinotan.listYears")
        sts, data = self.getPage(cItem['url'])
        if not sts: return
        data1 = self.cm.ph.getDataBeetwenMarkers(data, '<div class="navigright">', '</div>', False)[1]
        datay = re.compile('href="(/t.*?)">(.*?)</a><br>').findall(data1)
        for item in datay:
            params = dict(cItem)
            params.update({'category': category, 'title': item[1][:-2], 'url': self._getFullUrl(item[0][1:])})
            self.addDir(params)

    def listItems(self, cItem, category):
        printDBG("Kinotan.listItems")

        tmp = cItem['url'].split('?')
        url = tmp[0]
        if len(tmp) > 1:
            args = cItem.get('title', None)
            url = self.SRCH_URL+args

        page = cItem.get('page', 1)
        if page > 1:
            url += 'page/%s/' % page

        post_data = cItem.get('post_data', None)
        sts, data = self.getPage(url, {}, post_data)

        if not sts: return

        nextPage = False
        if ('/page/%s/' % (page + 1)) in data:
            nextPage = True

        data = self.cm.ph.getDataBeetwenMarkers(data, '<div class="short-item">', '</div></div>', False)[1]
        data = data.split('<div class="short-item">')
        for item in data:
            url = self.cm.ph.getSearchGroups(item, '<h3>.*"(.*?)">.*</a>')[0]
            icon = self.cm.ph.getSearchGroups(item, 'src="(.*?)"')[0][1:]
            icon = self._getFullUrl(icon)
            title = self.cm.ph.getSearchGroups(item, '<h3>.*".*">(.*?)</a>')[0]
            desc1 = self.cm.ph.getSearchGroups(item, 'label">(.*?)</div>')[0]
            desc2 = self.cm.ph.getSearchGroups(item, 'update3">(.*?)</div>')[0]
            desc = desc1 + ': ' + desc2
            params = dict(cItem)
            params.update({'category': category, 'title': title, 'icon': self._getFullUrl(icon), 'desc': desc, 'url': self._getFullUrl(url)})
            self.addDir(params)

        if nextPage:
            params = dict(cItem)
            params.update({'title': _('Next page'), 'page': cItem.get('page', 1) + 1})
            self.addDir(params)

    def listContent(self, cItem, category):
        printDBG("Kinotan.listContent")
        sts, data = self.getPage(cItem['url'])
        if not sts: return

        title = cItem['title']
        d_url = self.cm.ph.getDataBeetwenMarkers(data, '<div class="full-text">', '</iframe>', False)[1]
        url = re.compile('src="(.*?)"').findall(d_url)[0]
        if url.startswith('//'):
            url = 'http:' + url
        desc = self.cm.ph.getDataBeetwenMarkers(data, '<h2 class="opisnie">', '<div style="display', False)[1]
        desc = re.compile('>(.*?)</div>').findall(desc)[0]
        desc = self.cleanHtmlStr(desc)
        params = dict(cItem)
        params['desc'] = desc
        params['url'] = url
        hostName = self.up.getHostName(url)
        if hostName in ['serpens.nl', '37.220.36.15']:
            hostName = 'moonwalk.cc'
        if hostName == 'moonwalk.cc' and '/serial/' in url:
            params.update({'category': category, 'serie_title': title})
            season = self.moonwalkParser.getSeasonsList(url)
            for item in season:
                param = dict(params)
                param.update(
                    {'host_name': 'moonwalk', 'title': item['title'], 'season_id': item['id'], 'url': item['url']})
                self.addDir(param)
            return
        if 1 == self.up.checkHostSupport(url):
            self.addVideo(params)

    def listEpisodes(self, cItem):
        printDBG("Kinotan.listEpisodes")

        hostName = cItem['host_name']
        if hostName == 'moonwalk':
            title = cItem['serie_title']
            id = cItem['season_id']
            episodes = self.moonwalkParser.getEpiodesList(cItem['url'], id)

            for item in episodes:
                params = dict(cItem)
                params.update(
                    {'title': '{0} - s{1}e{2} {3}'.format(title, id, item['id'], item['title']), 'url': item['url']})
                self.addVideo(params)

    def listSearchResult(self, cItem, searchPattern, searchType):
        searchPattern = urllib.quote_plus(searchPattern)
        cItem = dict(cItem)
        cItem['url'] = self.SRCH_URL
        cItem['post_data'] = {'do': 'search', 'subaction': 'search', 'x': 0, 'y': 0, 'story': searchPattern}
        self.listItems(cItem, 'list_content')

    def getLinksForVideo(self, cItem):
        printDBG("Kinotan.getLinksForVideo [%s]" % cItem)
        urlTab = []
        urlTab.append({'name': 'Main url', 'url': cItem['url'], 'need_resolve': 1})
        return urlTab

    def getVideoLinks(self, videoUrl):
        printDBG("Kinotan.getVideoLinks [%s]" % videoUrl)
        urlTab = []
        if videoUrl.startswith('http'):
            urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab

    def getFavouriteData(self, cItem):
        return cItem['url']

    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url': fav_data})

    def handleService(self, index, refresh=0, searchPattern='', searchType=''):
        printDBG('handleService start')

        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        printDBG("handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category))
        self.currList = []

    # MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name': 'category'})
        elif category == 'cat_tv_shows':
            self.listItems(self.currItem, 'list_content')
        elif category == 'cat_mult':
            self.listItems(self.currItem, 'list_content')
    # SERIALES
        elif category == 'cat_serials':
            self.listsTab(self.SERIALS_CAT_TAB, {'name': 'category'})
        elif category == 'genre':
            self.listGenre(self.currItem, 'list_items')
        elif category == 'country':
            self.listCountry(self.currItem, 'list_items')
        elif category == 'trans':
            self.listTrans(self.currItem, 'list_items')
        elif category == 'sel':
            self.listSel(self.currItem, 'list_items')
        elif category == 'years':
            self.listYears(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem, 'list_content')
        elif category == 'list_content':
            self.listContent(self.currItem, 'list_episodes')
        elif category == 'list_episodes':
            self.listEpisodes(self.currItem)
    # SEARCH
        elif category in ["search", "search_next_page"]:
            cItem = dict(self.currItem)
            cItem.update({'search_item': False, 'name': 'category'})
            self.listSearchResult(cItem, searchPattern, searchType)
    # HISTORIA SEARCH
        elif category == "search_history":
            self.listsHistory({'name': 'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()

        CBaseHostClass.endHandleService(self, index, refresh)


class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, Kinotan(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('kinotanlogo.png')])

    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)

        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], item['need_resolve']))

        return RetHost(RetHost.OK, value = retlist)

    def getResolvedURL(self, url):
        retlist = []
        urlList = self.host.getVideoLinks(url)
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)

    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = []
        hostLinks = []
        type = CDisplayListItem.TYPE_UNKNOWN
        possibleTypesOfSearch = None
        if 'category' == cItem['type']:
            if cItem.get('search_item', False):
                type = CDisplayListItem.TYPE_SEARCH
                possibleTypesOfSearch = searchTypesOptions
            else:
                type = CDisplayListItem.TYPE_CATEGORY
        elif 'video' == cItem['type']:
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

    def getSearchItemInx(self):
        try:
            list = self.host.getCurrList()
            for i in range(len(list)):
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
                self.host.history.addHistoryItem(pattern, search_type)
                self.searchPattern = pattern
                self.searchType = search_type
        except:
            printDBG('setSearchPattern EXCEPTION')
            self.searchPattern = ''
            self.searchType = ''
        return
